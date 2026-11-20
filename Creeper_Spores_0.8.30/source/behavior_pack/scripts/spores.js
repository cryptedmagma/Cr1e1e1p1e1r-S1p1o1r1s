import { world, system, BlockPermutation, ItemStack } from "@minecraft/server";
import {
  NS, SPORE_BLOCK, STATE_AGE, STATE_ROT, STATE_STRAIN, MAX_AGE,
  randRot, randInt, getBlockSafe, belowOf, aboveOf, isFree, isSpore, hasSupport,
  getBiomeId, playersNear, enchantLevel, scaledCount, giveItem,
} from "./util.js";
import { STRAINS, VARIANTS } from "./generated_data.js";
import { pickMutation, pickVariant } from "./logic.js";
import { getConfig } from "./config.js";
import { record } from "./journal.js";
import { diag } from "./diag.js";
import { cue, sound, particle } from "./fx.js";
import { inZone } from "./zones.js";
import { migrate } from "./migrate.js";
import { substrateMultiplier } from "./tuning.js";
import { rememberPod } from "./atlas.js";

// ---------------------------------------------------------------------------
// Microscopic spores (not yet visible). Stored as world dynamic properties using the
// ORIGINAL key format  spores.<dimension>(x, y, z)  so spores from existing saves keep working.
//   legacy value : negative number of ticks still to wait
//   new value    : "<dueAbsoluteTime>:<strain>"
// The due time is absolute world time, so progress survives reloads without rewriting
// every record every tick (the original rewrote each pending record every tick).
// ---------------------------------------------------------------------------
const PREFIX = "spores.";
const KEY_RE = /^spores\.([^(]+)\((-?\d+),\s*(-?\d+),\s*(-?\d+)\)$/;
const BATCH = 150;
const pending = new Map();
let loaded = false;
let cursor = 0;

const makeKey = (dim, x, y, z) => `${PREFIX}${dim}(${x}, ${y}, ${z})`;

function loadPending() {
  migrate();                                   // one-time schema upgrade of legacy records before reading them
  const now = world.getAbsoluteTime();
  for (const id of world.getDynamicPropertyIds()) {
    if (!id.startsWith(PREFIX)) continue;
    const m = KEY_RE.exec(id);
    if (!m) continue;
    const v = world.getDynamicProperty(id);
    let due, strain = 0;
    if (typeof v === "number") due = now + Math.abs(v);
    else if (typeof v === "string") { const [d, s] = v.split(":"); due = Number(d); strain = Number(s) || 0; }
    else continue;
    if (!Number.isFinite(due)) continue;
    pending.set(id, { dim: m[1], x: +m[2], y: +m[3], z: +m[4], due, strain });
  }
  loaded = true;
}

function removePending(key) {
  pending.delete(key);
  try { world.setDynamicProperty(key, undefined); } catch { /* already gone */ }
}

/** Queues a microscopic spore. Returns false if the location is already queued or the cap is reached. */
export function addPending(dim, loc, strain = 0, delay) {
  if (!loaded) loadPending();
  const cfg = getConfig();
  if (pending.size >= cfg.maxPendingSpores) return false;
  if (inZone(dim.id, loc)) { diag("deposit_quarantined", { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) }); return false; }
  const x = Math.floor(loc.x), y = Math.floor(loc.y), z = Math.floor(loc.z);
  const key = makeKey(dim.id, x, y, z);
  if (pending.has(key)) return false;
  const wait = delay ?? randInt(cfg.germinationMinTicks, cfg.germinationMaxTicks);
  const due = world.getAbsoluteTime() + wait;
  try { world.setDynamicProperty(key, `${due}:${strain}`); } catch { return false; }
  pending.set(key, { dim: dim.id, x, y, z, due, strain });
  return true;
}

export function clearPendingNear(dimId, c, r) {
  if (!loaded) loadPending();
  for (const [key, p] of [...pending]) {
    if (p.dim === dimId && Math.abs(p.x - c.x) <= r && Math.abs(p.y - c.y) <= r && Math.abs(p.z - c.z) <= r) removePending(key);
  }
}

export function pendingCount() { return pending.size; }

/** Runs every 20 ticks; touches at most BATCH records per run. */
export function tickPending() {
  try {
    if (!loaded) loadPending();
    if (!pending.size) return;
    const now = world.getAbsoluteTime();
    const keys = [...pending.keys()];
    const n = Math.min(BATCH, keys.length);
    for (let i = 0; i < n; i++) {
      cursor = (cursor + 1) % keys.length;
      const key = keys[cursor];
      const rec = pending.get(key);
      if (!rec || rec.due > now) continue;
      let dim;
      try { dim = world.getDimension(rec.dim); } catch { removePending(key); continue; }
      const block = getBlockSafe(dim, rec);
      if (!block) continue;                       // chunk not loaded: wait, never write blind
      removePending(key);
      if (isFree(block) && hasSupport(belowOf(block))) germinate(block, rec.strain);
    }
  } catch { /* never let one bad record stop the colony system */ }
}

export function germinate(block, strain, startAge = 0) {
  const age = Math.max(0, Math.min(MAX_AGE, Math.floor(startAge)));
  block.setPermutation(BlockPermutation.resolve(SPORE_BLOCK, { [STATE_ROT]: randRot(), [STATE_AGE]: age, [STATE_STRAIN]: strain }));
  sound(block.dimension, "hit.grass", block.location);
}

// ---------------------------------------------------------------------------
// Visible pod: growth, mutation, hatching
// ---------------------------------------------------------------------------
function neighbourIds(block) {
  const out = [];
  for (const [dx, dy, dz] of [[0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0]]) {
    const b = getBlockSafe(block.dimension, { x: block.x + dx, y: block.y + dy, z: block.z + dz });
    if (b) out.push(b.typeId);
  }
  return out;
}

function sporeTick(block) {
  const below = belowOf(block);
  if (!hasSupport(below)) { block.setType("minecraft:air"); return; }
  const perm = block.permutation;
  const age = perm.getState(STATE_AGE);
  const strain = perm.getState(STATE_STRAIN) ?? 0;
  const cfg = getConfig();
  noteKnown(block);
  for (const h of podHooks) { try { h(block, age, strain, cfg); } catch (e) { diag("pod_hook_error", { err: String(e).slice(0, 80) }); } }
  if (age >= 4 && !isFree(aboveOf(block))) return;            // original rule: swollen pods need room above
  const chance = cfg.growthAdvanceChance * (STRAINS[strain]?.growth ?? 1) * substrateMultiplier(below?.typeId);
  if (chance < 1 && Math.random() > chance) return;           // dormant this tick; tries again next random tick

  if (age < MAX_AGE) {
    let next = perm.withState(STATE_AGE, age + 1);
    if (age + 1 === 4 && strain === 0 && Math.random() < cfg.mutationChance) {
      const m = pickMutation(neighbourIds(block), cfg.mutationOutcomes);            // one candidate, one write
      if (m > 0) next = next.withState(STATE_STRAIN, m);
    }
    block.setPermutation(next);
    // Above-baseline growth: an independently verified extra age may occur after a delay.
    // Never jump two stages in the same tick, and preserve the stage-4 mutation checkpoint.
    if (chance > 1 && age < 5 && age !== 2 && Math.random() < Math.min(1, chance - 1)) {
      const dim = block.dimension, p = { ...block.location }, expectedStrain = next.getState(STATE_STRAIN) ?? 0;
      system.runTimeout(() => {
        try {
          const fresh = getBlockSafe(dim, p);
          if (!isSpore(fresh) || !hasSupport(belowOf(fresh))) return;
          if (fresh.permutation.getState(STATE_AGE) !== age + 1) return;
          if ((fresh.permutation.getState(STATE_STRAIN) ?? 0) !== expectedStrain) return;
          fresh.setPermutation(fresh.permutation.withState(STATE_AGE, age + 2));
        } catch { /* unloaded, replaced, or invalid: skip only this bonus */ }
      }, 20);
    }
    sound(block.dimension, "hit.grass", block.location);
    if (age + 1 === 4 && next.getState(STATE_STRAIN) !== strain) sound(block.dimension, "cookiedookie.bubble", block.location);
  } else {
    hatch(block, perm, strain);
  }
}

function isPeaceful() {
  try { return String(world.getDifficulty()).toLowerCase() === "peaceful"; } catch { return false; }
}

const clear = (b) => !!b && !b.isSolid;                       // passable for a newborn (air, liquid, plants)

function headroomOk(block, height) {
  const need = Math.ceil(height) - 1;
  for (let i = 1; i <= need; i++) {
    const b = getBlockSafe(block.dimension, { x: block.x, y: block.y + i, z: block.z });
    if (!b) return "unloaded";
    if (!clear(b)) return "no_headroom";
  }
  return "ok";
}

/**
 * Preflight for hatching. Pure checks, no writes. Returns { ok:true, ... } or { ok:false, reason }.
 * Everything that can make a spawn illegal is checked BEFORE a pod is touched.
 */
function hatchPlan(block, strain, reuse) {
  const cfg = getConfig();
  if (!cfg.hatchEnabled) return { ok: false, reason: "disabled" };
  if (isPeaceful()) return { ok: false, reason: "peaceful" };
  if (inZone(block.dimension.id, block.location)) return { ok: false, reason: "quarantine" };
  const dim = block.dimension;
  const center = { x: block.x + 0.5, y: block.y, z: block.z + 0.5 };

  // loaded space: the pod column and its four neighbours must all be readable
  for (const [dx, dz] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]]) {
    if (!getBlockSafe(dim, { x: block.x + dx, y: block.y, z: block.z + dz })) return { ok: false, reason: "unloaded" };
  }
  if (!hasSupport(belowOf(block))) return { ok: false, reason: "no_support" };

  try {
    if (dim.getEntities({ location: center, maxDistance: 24, families: ["creeper"] }).length >= cfg.maxCreepersNear)
      return { ok: false, reason: "creeper_cap" };
    // something already standing in the spawn cell (players excluded from blocking would be exploitable; they block)
    const occupied = dim.getEntities({ location: center, maxDistance: 0.7, excludeTypes: ["minecraft:item", "minecraft:xp_orb"] });
    if (occupied.length) return { ok: false, reason: "occupied" };
  } catch { /* entity queries unavailable: continue, the spawn itself is still guarded */ }

  let key = reuse?.key ?? null;
  let def = key ? VARIANTS[key] : null;
  if (!reuse) {
    let inWater = false;
    try { inWater = block.isWaterlogged === true; } catch { /* property absent */ }
    key = pickVariant({ strain, below: belowOf(block)?.typeId, dim: dim.id, biome: getBiomeId(dim, center), y: block.y, inWater, nearIds: neighbourIds(block) }, cfg.variantChance);
    def = key ? VARIANTS[key] : null;
  }
  let room = headroomOk(block, def ? def.height : 1.7);
  if (room === "unloaded") return { ok: false, reason: "unloaded" };
  if (room !== "ok" && def) {                                 // big/airborne variant doesn't fit: fall back to a vanilla creeper
    diag("hatch_variant_fallback_headroom", { variant: key });
    key = null; def = null;
    room = headroomOk(block, 1.7);
  }
  if (room !== "ok") return { ok: false, reason: room };
  return { ok: true, key, def, center };
}

// ---- extension points -------------------------------------------------------------
/** Hooks run on every visible pod tick: (block, age, strain, cfg). Used by ecology/colony spread. Errors are isolated. */
export const podHooks = [];
const known = new Map();                                       // "dim:x:y:z" -> last tick seen; in-memory colony registry for the compass
const KNOWN_MAX = 2000;
function noteKnown(block) {
  const k = `${block.dimension.id}:${block.x}:${block.y}:${block.z}`;
  known.delete(k); known.set(k, { dim: block.dimension.id, x: block.x, y: block.y, z: block.z });
  rememberPod(block.dimension.id,block.location,block.permutation.getState(STATE_STRAIN)??0);
  if (known.size > KNOWN_MAX) known.delete(known.keys().next().value);
}
export function nearestKnownPod(dimId, loc, maxDist = 128) {
  let best = null, bestD = maxDist * maxDist;
  for (const [key, p] of known) {
    if (p.dim !== dimId) continue;
    const dx = p.x - loc.x, dy = p.y - loc.y, dz = p.z - loc.z, dd = dx * dx + dy * dy + dz * dz;
    if (dd < bestD) { bestD = dd; best = { x: p.x, y: p.y, z: p.z, dist: Math.sqrt(dd), key }; }
  }
  return best;
}
export function knownPods(dimId, loc, maxDist = 256, limit = 12) {
  const out = []; const radius2 = maxDist * maxDist;
  for (const [key, p] of known) {
    if (p.dim !== dimId) continue;
    const dx = p.x - loc.x, dy = p.y - loc.y, dz = p.z - loc.z, d = dx*dx+dy*dy+dz*dz;
    if (d <= radius2) out.push({ ...p, dist: Math.sqrt(d), key });
  }
  return out.sort((a,b) => a.dist - b.dist).slice(0,limit);
}
export function forgetKnown(key) { known.delete(key); }

const hatching = new Map();                                   // pod key -> start tick (in-memory: a reload simply restarts the pod's wait)
const podKey = (b) => `${b.dimension.id}:${b.x}:${b.y}:${b.z}`;

function puff(dim, loc, id) { particle(dim, id, loc, { essential: true }); }   // cosmetic only; never decides success

function hatch(block, perm, strain) {
  const cfg = getConfig();
  const k = podKey(block);
  if (hatching.has(k)) return;                                // already mid-sequence: a second tick must not start another
  const plan = hatchPlan(block, strain);
  if (!plan.ok) { diag(`hatch_${plan.reason}`, { x: block.x, y: block.y, z: block.z, dim: block.dimension.id }); return; }

  if (!cfg.hatchAnimation) { completeHatch(block, strain, plan); return; }

  // Sequence: shake (0-30 ticks) -> shell bursts -> spawn. Cosmetic cues only; the spawn below re-validates everything.
  hatching.set(k, system.currentTick);
  const dim = block.dimension, pos = block.location;
  // Purely visual shell pieces animate open; the original pod controls the actual spawn.
  try { dim.spawnEntity(`${NS}:spore_shell`, { x: pos.x + 0.5, y: pos.y + 0.25, z: pos.z + 0.5 }); }
  catch { diag("shell_visual_unavailable"); }
  const mid = { x: pos.x + 0.5, y: pos.y + 0.6, z: pos.z + 0.5 };
  const stillSame = () => {
    const b = getBlockSafe(dim, pos);
    return isSpore(b) && b.permutation.getState(STATE_AGE) === MAX_AGE && (b.permutation.getState(STATE_STRAIN) ?? 0) === strain ? b : undefined;
  };
  const step = (n) => {
    try {
      const b = stillSame();
      if (!b) { hatching.delete(k); diag("hatch_cancelled_source_changed", { x: pos.x, y: pos.y, z: pos.z }); return; }
      if (n < 3) {
        puff(dim, mid, "minecraft:villager_happy");
        puff(dim, mid, "cookiedookie:spore_mote");
        sound(dim, "cookiedookie.rumble", pos, { volume: 0.8 });
        system.runTimeout(() => step(n + 1), 10);
      } else {
        const fresh = hatchPlan(b, strain, plan);              // reuse the chosen variant, re-check every other condition
        hatching.delete(k);
        if (!fresh.ok) { diag(`hatch_${fresh.reason}_at_emerge`, { x: pos.x, y: pos.y, z: pos.z }); return; }
        puff(dim, mid, "minecraft:egg_destroy_emitter");        // shell opens
        puff(dim, mid, "cookiedookie:spore_burst");
        sound(dim, "mob.turtle_egg.crack", pos, { volume: 0.8 });
        sound(dim, "cookiedookie.pod_pop", pos);
        completeHatch(b, strain, fresh);
      }
    } catch (e) { hatching.delete(k); diag("hatch_sequence_error", { err: String(e).slice(0, 80) }); }
  };
  step(0);
}

/** Spawn first, consume the pod only if a creeper actually exists. */
function completeHatch(block, strain, plan) {
  const cfg = getConfig();
  const dim = block.dimension;
  const perm = block.permutation;
  const rotation = Number(perm.getState(STATE_ROT));
  let entity, usedDef = plan.def;
  try {
    entity = dim.spawnEntity(usedDef ? usedDef.id : "minecraft:creeper", plan.center, { initialRotation: 180 - rotation });
  } catch (e) {
    diag("hatch_spawn_failed", { variant: plan.key, err: String(e).slice(0, 80) });
    if (usedDef) {                                            // custom entity unavailable (e.g. pack mismatch): fall back instead of stalling forever
      try { entity = dim.spawnEntity("minecraft:creeper", plan.center, { initialRotation: 180 - rotation }); usedDef = null; diag("hatch_fallback_vanilla_ok", { variant: plan.key }); } catch { entity = undefined; }
    }
  }
  if (!entity) return;                                        // failed spawn keeps the pod untouched

  try {                                                       // first-spawn identity, written once
    entity.addTag("cs_hatched");
    entity.setDynamicProperty("cs:strain", strain);
    entity.setDynamicProperty("cs:src", `${dim.id}:${block.x}:${block.y}:${block.z}`);
  } catch { /* entity vanished instantly; pod handling below still follows the real spawn result */ }
  if (usedDef && cfg.emergenceStages) {
    try { entity.triggerEvent("cookiedookie:emerge"); } catch (e) { diag("emerge_event_failed", { err: String(e).slice(0, 80) }); }
  }
  block.setPermutation(perm.withState(STATE_AGE, 0));          // pod resets and regrows (original behaviour)
  puff(dim, { x: block.x + 0.5, y: block.y + 0.8, z: block.z + 0.5 }, "minecraft:villager_happy");
  sound(dim, "cookiedookie.hiss", block.location, { volume: 0.7 });
  for (const p of playersNear(dim, plan.center, 32)) record(p, "hatch", usedDef ? plan.key : null);
}

// ---------------------------------------------------------------------------
// Registration + world events
// ---------------------------------------------------------------------------
export function registerBlock(registry) {
  registry.registerCustomComponent(`${NS}:creeper_spores`, {
    beforeOnPlayerPlace(data) {
      data.cancel = !hasSupport(belowOf(data.block));
      data.permutationToPlace = data.permutationToPlace.withState(STATE_ROT, randRot());
    },
    onTick({ block }) {
      try { sporeTick(block); } catch { /* a transient error must not kill the tick loop */ }
    },
  });
}

/** Direct placement used by seed items. */
export function plantSpore(block, strain) {
  block.setPermutation(BlockPermutation.resolve(SPORE_BLOCK, { [STATE_ROT]: randRot(), [STATE_AGE]: 0, [STATE_STRAIN]: strain }));
}

/** Resource drops for a pod of a given age/strain (used by breaking, collector, shears). */
export function podYield(age, strain, mult = 1) {
  const cfg = getConfig();
  const out = [];
  if (age >= 3) out.push([`${NS}:spore_extract`, scaledCount(1 + (age >= 6 ? 1 : 0), cfg.harvestYield * mult)]);
  const drop = STRAINS[strain]?.drop;
  if (drop && age >= 5 && Math.random() < 0.5) out.push([`${NS}:${drop}`, scaledCount(1, cfg.harvestYield)]);
  // Sparse bonus drops from mature growth; avoid adding unrelated resources to young pods.
  if(age>=6 && strain===1 && Math.random()<0.08) out.push([`${NS}:fungal_crystal`,1]);
  if(age>=6 && (strain===0||strain===1) && Math.random()<0.09) out.push([`${NS}:glowing_thread`,1]);
  if(age>=5 && (strain===2||strain===0) && Math.random()<0.10) out.push([`${NS}:spore_pigment`,1]);
  return out.filter(([, n]) => n > 0);
}

world.beforeEvents.playerPlaceBlock.subscribe(data => {
  const b = belowOf(data.block);
  data.cancel = !!b && b.typeId === SPORE_BLOCK && b.permutation.getState(STATE_AGE) >= 5;   // original rule
});

world.afterEvents.playerBreakBlock.subscribe(({ block, player, brokenBlockPermutation, itemStackBeforeBreak }) => {
  try {
    const above = aboveOf(block);
    if (above?.typeId === SPORE_BLOCK) above.setType("minecraft:air");
    if (brokenBlockPermutation?.type?.id === SPORE_BLOCK) {
      const age = brokenBlockPermutation.getState(STATE_AGE);
      const strain = brokenBlockPermutation.getState(STATE_STRAIN) ?? 0;
      if (String(player.getGameMode()).toLowerCase() !== "creative") {
        if (enchantLevel(itemStackBeforeBreak, "silk_touch") > 0) {
          giveItem(player, strain === 0 ? `${NS}:creeper_spores` : `${NS}:seed_${STRAINS[strain].key}`, 1);   // silk touch lifts the pod as a seed
        } else {
          const f = enchantLevel(itemStackBeforeBreak, "fortune");
          giveYield(player, age, strain, 1 + f * 0.25);
        }
      }
      record(player, "strain", STRAINS[strain]?.key);
    }
  } catch { /* cosmetic/reward failure never undoes the break */ }
});
world.afterEvents.blockExplode.subscribe(({ block }) => {
  try { const above = aboveOf(block); if (above?.typeId === SPORE_BLOCK) above.setType("minecraft:air"); } catch { /* chunk edge */ }
});

export function giveYield(player, age, strain, mult = 1) {
  for (const [id, n] of podYield(age, strain, mult)) giveItem(player, id, n);
}
