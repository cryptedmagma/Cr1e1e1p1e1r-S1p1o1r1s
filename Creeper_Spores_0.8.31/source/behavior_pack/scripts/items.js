import { world, system, BlockPermutation } from "@minecraft/server";
import {
  NS, SPORE_BLOCK, STATE_AGE, STATE_ROT, STATE_STRAIN, MAX_AGE,
  getBlockSafe, belowOf, isFree, isSpore, hasSupport, isCreative, lockOnce, giveItem,
  playSound, sendActionBar, enchantLevel,
} from "./util.js";
import { STRAINS, SEED_ITEMS } from "./generated_data.js";
import { STRAIN_INDEX } from "./logic.js";
import { plantSpore, podYield, clearPendingNear, nearestKnownPod, forgetKnown } from "./spores.js";
import { addZone } from "./zones.js";
import { sound, particle } from "./fx.js";
import { record, openJournal } from "./journal.js";
import { cureNear } from "./terrain.js";

const DIR = { Up: [0, 1, 0], Down: [0, -1, 0], North: [0, 0, -1], South: [0, 0, 1], East: [1, 0, 0], West: [-1, 0, 0] };

function faceTarget(block, face) {
  const d = DIR[face];
  if (!d) return undefined;
  return getBlockSafe(block.dimension, { x: block.x + d[0], y: block.y + d[1], z: block.z + d[2] });
}

function mainhand(player) {
  try { return player.getComponent("equippable")?.getEquipment("Mainhand"); } catch { return undefined; }
}

/** Uses one of the held stack (not in Creative). Validates the held item is still what we expect. */
function consume(player, expectedId) {
  if (isCreative(player)) return true;
  try {
    const eq = player.getComponent("equippable");
    const it = eq.getEquipment("Mainhand");
    if (!it || it.typeId !== expectedId) return false;
    if (it.amount > 1) { it.amount -= 1; eq.setEquipment("Mainhand", it); }
    else eq.setEquipment("Mainhand", undefined);
    return true;
  } catch { return false; }
}

function damageTool(player, expectedId, amount = 1) {
  if (isCreative(player)) return;
  try {
    const eq = player.getComponent("equippable");
    const it = eq.getEquipment("Mainhand");
    if (!it || it.typeId !== expectedId) return;
    const d = it.getComponent("minecraft:durability");
    if (!d) return;
    if (d.damage + amount >= d.maxDurability) { eq.setEquipment("Mainhand", undefined); playSound(player.dimension, "random.break", player.location, 1); }
    else { d.damage += amount; eq.setEquipment("Mainhand", it); }
  } catch { /* durability is best-effort */ }
}

function podInfo(block) {
  const age = block.permutation.getState(STATE_AGE);
  const strain = block.permutation.getState(STATE_STRAIN) ?? 0;
  return { age, strain, s: STRAINS[strain] };
}

function describe(block) {
  const { age, s } = podInfo(block);
  const phase = age === 7 ? "ready to hatch" : age >= 4 ? "pod swelling" : age >= 2 ? "sprouting" : "seed";
  return `§a${s.name}§r  Stage ${age + 1}/${MAX_AGE + 1} (${phase})  Ground: ${belowOf(block)?.typeId?.replace("minecraft:", "") ?? "?"}`;
}

const cooldowns = new Map();
function cooling(key, ticks) {
  const now = system.currentTick;
  if ((cooldowns.get(key) ?? -1e9) + ticks > now) return true;
  cooldowns.set(key, now);
  if (cooldowns.size > 512) cooldowns.delete(cooldowns.keys().next().value);
  return false;
}

// ---- harvesting (collector / shears) --------------------------------------
function harvest(player, block, toolId) {
  if (!isSpore(block)) return false;
  const { age, strain } = podInfo(block);
  if (age < 3) { sendActionBar(player, "§7Too young to harvest."); return false; }
  const drops = podYield(age, strain);
  block.setPermutation(block.permutation.withState(STATE_AGE, 1));        // strain and rotation preserved
  for (const [id, n] of drops) giveItem(player, id, n);
  damageTool(player, toolId, 1);
  record(player, "harvest");
  record(player, "strain", STRAINS[strain]?.key);
  playSound(block.dimension, "dig.grass", block.location);
  return true;
}

// ---- custom item components -----------------------------------------------
export function registerItems(reg) {
  reg.registerCustomComponent(`${NS}:seed`, {
    onUseOn(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player") return;
      const strain = SEED_ITEMS[e.itemStack.typeId];
      if (strain === undefined) return;
      const target = faceTarget(e.block, e.blockFace);
      if (!target || !isFree(target) || !hasSupport(belowOf(target))) { sendActionBar(player, "§7Spores need firm ground."); return; }
      if (!lockOnce(`seed:${player.id}`, system.currentTick)) return;
      if (!consume(player, e.itemStack.typeId)) return;
      plantSpore(target, strain);
      playSound(target.dimension, "hit.grass", target.location);
      record(player, "plant", STRAINS[strain].key);
    },
  });

  reg.registerCustomComponent(`${NS}:scanner`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`scan:${player.id}`, 10)) return;
      const hit = player.getBlockFromViewDirection({ maxDistance: 6 });
      const block = hit?.block;
      if (!isSpore(block)) { sendActionBar(player, "§7Nothing to scan."); return; }
      sendActionBar(player, describe(block));
      damageTool(player, e.itemStack.typeId, 1);
      record(player, "scan", podInfo(block).s.key);
    },
  });

  reg.registerCustomComponent(`${NS}:detector`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`det:${player.id}`, 20)) return;
      const R = 8, dim = player.dimension;
      const o = { x: Math.floor(player.location.x), y: Math.floor(player.location.y), z: Math.floor(player.location.z) };
      let count = 0, best = null, bestD = 1e9;
      for (let x = -R; x <= R; x++) for (let y = -R; y <= R; y++) for (let z = -R; z <= R; z++) {
        const b = getBlockSafe(dim, { x: o.x + x, y: o.y + y, z: o.z + z });
        if (!isSpore(b)) continue;
        count++;
        const d = x * x + y * y + z * z;
        if (d < bestD) { bestD = d; best = [x, z]; }
      }
      if (!count) { sendActionBar(player, "§7No spores within 8 blocks."); damageTool(player, e.itemStack.typeId, 1); return; }
      const ang = Math.atan2(best[1], best[0]) * 180 / Math.PI;                // 0 = +x (east), 90 = +z (south)
      const dirs = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"];
      const dir = dirs[Math.round(((ang + 360) % 360) / 45) % 8];
      sendActionBar(player, `§e${count}§r spore${count === 1 ? "" : "s"} nearby. Nearest: §a${Math.round(Math.sqrt(bestD))}m ${dir}§r`);
      damageTool(player, e.itemStack.typeId, 1);
      record(player, "detect");
    },
  });

  reg.registerCustomComponent(`${NS}:collector`, {
    onUseOn(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player") return;
      if (!lockOnce(`col:${player.id}`, system.currentTick)) return;
      harvest(player, e.block, e.itemStack.typeId);
    },
  });

  reg.registerCustomComponent(`${NS}:purifier`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`pur:${player.id}`, 20)) return;
      const R = 4, dim = player.dimension;
      const o = { x: Math.floor(player.location.x), y: Math.floor(player.location.y), z: Math.floor(player.location.z) };
      let removed = 0;
      for (let x = -R; x <= R; x++) for (let y = -R; y <= R; y++) for (let z = -R; z <= R; z++) {
        const b = getBlockSafe(dim, { x: o.x + x, y: o.y + y, z: o.z + z });
        if (isSpore(b)) { b.setType("minecraft:air"); removed++; }
      }
      clearPendingNear(dim.id, o, R);
      const restored = cureNear(dim, o, R, 36);
      if (restored) removed += restored;
      if (removed) { damageTool(player, e.itemStack.typeId, 1 + Math.floor(removed / 4)); playSound(dim, "random.fizz", player.location, 1); record(player, "purge"); }
      sendActionBar(player, removed ? `§bPurified ${removed} growth${removed === 1 ? "" : "s"}.` : "§7Nothing to purify.");
    },
  });

  reg.registerCustomComponent(`${NS}:catalyst`, {
    onUseOn(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || !isSpore(e.block)) return;
      const { age, strain } = podInfo(e.block);
      if (age < 5 || strain === STRAIN_INDEX.royal) { sendActionBar(player, "§7Needs a swollen, non-royal pod."); return; }
      if (!lockOnce(`cat:${player.id}`, system.currentTick)) return;
      if (!consume(player, e.itemStack.typeId)) return;
      e.block.setPermutation(e.block.permutation.withState(STATE_STRAIN, STRAIN_INDEX.royal));
      playSound(e.block.dimension, "random.levelup", e.block.location, 1);
      record(player, "strain", "royal");
    },
  });

  // Sprayer: opens a time-limited quarantine zone (no NEW placement / hatching inside). Existing growths stay.
  reg.registerCustomComponent(`${NS}:sprayer`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`spr:${player.id}`, 40)) return;
      const z = addZone(player.dimension.id, player.location, 6, 6000);
      if (!z) return;
      damageTool(player, e.itemStack.typeId, 1);
      particle(player.dimension, { x: player.location.x, y: player.location.y + 1, z: player.location.z }, "minecraft:villager_happy", { essential: true });
      sound(player.dimension, "random.fizz", player.location);
      sendActionBar(player, "§bQuarantine zone active: 6 blocks, 5 minutes.");
      record(player, "zone");
    },
  });

  // Vacuum: removes microscopic spores and young pods (age <= 2) nearby; mature pods are left for harvesting.
  reg.registerCustomComponent(`${NS}:vacuum`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`vac:${player.id}`, 20)) return;
      const R = 4, dim = player.dimension;
      const o = { x: Math.floor(player.location.x), y: Math.floor(player.location.y), z: Math.floor(player.location.z) };
      let removed = 0;
      for (let x = -R; x <= R; x++) for (let y = -2; y <= 2; y++) for (let z = -R; z <= R; z++) {
        const b = getBlockSafe(dim, { x: o.x + x, y: o.y + y, z: o.z + z });
        if (isSpore(b) && b.permutation.getState(STATE_AGE) <= 2) { b.setType("minecraft:air"); removed++; }
      }
      clearPendingNear(dim.id, o, R);
      if (!removed) { sendActionBar(player, "§7Nothing small enough to vacuum."); return; }
      giveItem(player, `${NS}:spore_extract`, Math.floor(removed / 2) + (removed % 2 && Math.random() < 0.5 ? 1 : 0));
      damageTool(player, e.itemStack.typeId, 1);
      record(player, "purge");
      sound(dim, "random.pop", player.location);
      sendActionBar(player, `§bVacuumed ${removed} young growth${removed === 1 ? "" : "s"}.`);
    },
  });

  // Compass: points toward the nearest pod this world session has seen tick (re-verified when used).
  reg.registerCustomComponent(`${NS}:compass`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`cmp:${player.id}`, 20)) return;
      const hit = nearestKnownPod(player.dimension.id, player.location, 128);
      if (!hit) { sendActionBar(player, "§7No known colonies nearby."); return; }
      if (!isSpore(getBlockSafe(player.dimension, hit))) { forgetKnown(hit.key); sendActionBar(player, "§7That colony is gone. Try again."); return; }
      const ang = Math.atan2(hit.z - player.location.z, hit.x - player.location.x) * 180 / Math.PI;
      const dir = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"][Math.round(((ang + 360) % 360) / 45) % 8];
      sendActionBar(player, `§aNearest known colony: ${Math.round(hit.dist)}m ${dir}§r`);
    },
  });

  reg.registerCustomComponent(`${NS}:journal`, {
    onUse(e) {
      const player = e.source;
      if (player?.typeId !== "minecraft:player" || cooling(`jrn:${player.id}`, 10)) return;
      system.run(() => { openJournal(player); });
    },
  });
}

// ---- vanilla tools on pods ------------------------------------------------
// Each action: held item must still match and the pod must still exist when the delayed write runs.
const SHOVELS = new Set(["minecraft:iron_shovel", "minecraft:diamond_shovel", "minecraft:netherite_shovel"]);
const PICKS = new Set(["minecraft:iron_pickaxe", "minecraft:diamond_pickaxe", "minecraft:netherite_pickaxe"]);
const VANILLA = new Set(["minecraft:shears", "minecraft:bone_meal", "minecraft:flint_and_steel", "minecraft:fire_charge",
  "minecraft:brush", "minecraft:glass_bottle", "minecraft:water_bucket", "minecraft:lava_bucket", "minecraft:diamond_hoe",
  ...SHOVELS, ...PICKS]);

function seedFor(strain) { return strain === 0 ? `${NS}:creeper_spores` : `${NS}:seed_${STRAINS[strain].key}`; }

function burn(player, block, id, pos, dim, age, strain) {
  if (strain === STRAIN_INDEX.ember) { sendActionBar(player, "§6Ember spores shrug off the flame."); return; }
  if (id === "minecraft:fire_charge") { if (!consume(player, id)) return; } else if (id === "minecraft:flint_and_steel") damageTool(player, id, 1);
  block.setType("minecraft:air");
  if (age >= 5 && Math.random() < 0.4) giveItem(player, `${NS}:volatile_essence`, 1);
  playSound(dim, "fire.ignite", pos, 1);
}

function lift(player, block, id) {                                  // shovel / silk-touch pickaxe: take the pod up intact as a seed
  const { age, strain } = podInfo(block);
  if (age < 1) { sendActionBar(player, "§7Too small to lift."); return; }
  if (id.endsWith("_pickaxe")) {
    const held = mainhand(player);
    if (enchantLevel(held, "silk_touch") < 1) { sendActionBar(player, "§7Needs Silk Touch."); return; }
  }
  block.setType("minecraft:air");
  giveItem(player, seedFor(strain), 1);
  damageTool(player, id, 1);
  playSound(block.dimension, "dig.grass", block.location);
}

world.beforeEvents.playerInteractWithBlock.subscribe(ev => {
  const item = ev.itemStack;
  if (!item || !VANILLA.has(item.typeId) || ev.isFirstEvent === false) return;
  const b = ev.block;
  if (b.typeId !== SPORE_BLOCK) return;
  ev.cancel = true;                                                   // we own the interaction (also stops bucket placement)
  const player = ev.player, dim = b.dimension, pos = b.location, id = item.typeId;
  system.run(() => {
    try {
      if (player.isValid === false) return;
      if (!lockOnce(`vt:${player.id}`, system.currentTick)) return;
      const block = getBlockSafe(dim, pos);
      if (!isSpore(block)) return;                                       // replaced/removed since the click
      if (mainhand(player)?.typeId !== id) return;                       // hotbar changed
      const { age, strain } = podInfo(block);
      if (id === "minecraft:brush") { sendActionBar(player, describe(block)); record(player, "scan", STRAINS[strain].key); }
      else if (id === "minecraft:shears") harvest(player, block, id);
      else if (id === "minecraft:bone_meal") {
        if (age >= MAX_AGE) { sendActionBar(player, "§7Already mature."); return; }
        if (!consume(player, id)) return;
        block.setPermutation(block.permutation.withState(STATE_AGE, age + 1));
        particle(dim, { x: pos.x + 0.5, y: pos.y + 0.5, z: pos.z + 0.5 }, "minecraft:crop_growth_emitter", { essential: true });
      } else if (id === "minecraft:flint_and_steel" || id === "minecraft:fire_charge" || id === "minecraft:lava_bucket") {
        burn(player, block, id === "minecraft:lava_bucket" ? "minecraft:lava_bucket" : id, pos, dim, age, strain);   // lava bucket is not consumed
      } else if (id === "minecraft:water_bucket") {
        if (age < 5) { sendActionBar(player, "§7Only swollen pods need dousing."); return; }
        addZone(dim.id, pos, 3, 2400);                                    // temporary hatch suppression; bucket is kept
        sendActionBar(player, "§bPod doused: hatching suppressed nearby for 2 minutes.");
        record(player, "zone");
      } else if (id === "minecraft:glass_bottle") {
        if (age < 3) { sendActionBar(player, "§7Too young."); return; }
        if (!consume(player, id)) return;
        giveItem(player, `${NS}:spore_extract`, 1);
        block.setPermutation(block.permutation.withState(STATE_AGE, Math.max(1, age - 2)));
      } else if (id === "minecraft:diamond_hoe") {
        if (age >= 3) { sendActionBar(player, "§7Hoe only coaxes young sprouts."); return; }
        block.setPermutation(block.permutation.withState(STATE_AGE, age + 1));
        damageTool(player, id, 1);
      } else if (SHOVELS.has(id) || PICKS.has(id)) lift(player, block, id);
    } catch { /* stale interaction: ignore */ }
  });
});
