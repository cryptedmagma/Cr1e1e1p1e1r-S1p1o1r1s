import { armorBlocksEffect } from "./protection.js";
import { world, system } from "@minecraft/server";
import {
  getBlockSafe, belowOf, isFree, hasSupport, getBiomeId, blockedBetween, isSurvivalLike,
} from "./util.js";
import { getConfig } from "./config.js";
import { pickStrain, variantFromTypeId } from "./logic.js";
import { addPending, germinate } from "./spores.js";
import { inZone } from "./zones.js";
import { diag } from "./diag.js";

/**
 * Creeper-family explosions release spores (vanilla creepers plus every custom variant).
 * Other blast types are intentionally not enabled yet.
 */
// Subscribe to both phases. A before-event can exist but omit its source on some
// engine builds; subscribing only to it would silently miss a vanilla Creeper blast.
// Both callbacks copy primitive/entity data immediately, then defer world writes.
const recentlyHandledBlasts = new Map();
function subscribeBlastSignal(signal, phase) {
  if (!signal?.subscribe) return false;
  try {
    signal.subscribe(ev => {
      try {
        const src = ev.source;
        if (!src) { diag(`blast_missing_source_${phase}`); return; }
        const typeId = src.typeId;
        const info = variantFromTypeId(typeId);
        if (!info) {
          if (String(typeId).includes("creeper")) diag("blast_unknown_creeper_source", { typeId, phase });
          return;
        }
        const dim = ev.dimension;
        const loc = { x: src.location.x, y: src.location.y, z: src.location.z };
        const tick = system.currentTick;
        // The same blast can arrive through both event phases on the same or
        // adjacent ticks. Deduplicate those callbacks without suppressing a later blast.
        for (const [key, expiry] of recentlyHandledBlasts) if (expiry < tick) recentlyHandledBlasts.delete(key);
        const blastKey = `${dim.id}:${typeId}:${Math.floor(loc.x)}:${Math.floor(loc.y)}:${Math.floor(loc.z)}`;
        if ((recentlyHandledBlasts.get(blastKey) ?? -1) >= tick) return;
        recentlyHandledBlasts.set(blastKey, tick + 4);
        if (recentlyHandledBlasts.size > 64) recentlyHandledBlasts.delete(recentlyHandledBlasts.keys().next().value);

        let charged = false;
        try { charged = src.hasComponent("minecraft:is_charged"); } catch { /* component query unsupported */ }
        let srcStrain = info.def ? info.def.strain : 0;
        try { const strain = src.getDynamicProperty("cs:strain"); if (typeof strain === "number") srcStrain = strain; } catch { /* no stored strain */ }
        const job = { dim, loc, charged, srcStrain, def: info.def };
        system.run(() => { try { release(job); } catch (e) { diag("blast_release_error", { err: String(e).slice(0, 100), phase }); } });
      } catch (e) { diag("blast_event_error", { err: String(e).slice(0, 100), phase }); }
    });
    return true;
  } catch (e) {
    diag("blast_event_subscribe_error", { phase, err: String(e).slice(0, 80) });
    return false;
  }
}
const hasBeforeBlast = subscribeBlastSignal(world.beforeEvents?.explosion, "before");
const hasAfterBlast = subscribeBlastSignal(world.afterEvents?.explosion, "after");
if (!hasBeforeBlast && !hasAfterBlast) diag("blast_event_unavailable");

function release({ dim, loc, charged, srcStrain, def }) {
  const cfg = getConfig();
  let radius = charged ? cfg.radiusCharged : cfg.radiusNormal;
  radius = Math.max(1, Math.min(16, Math.round(radius * (def?.rmul ?? 1))));

  const biome = getBiomeId(dim, loc);
  if (def?.effect) applyEffect(dim, loc, def.effect);
  if (cfg.deepDarkBlocksNatural && typeof biome === "string" && biome.includes("deep_dark")) { diag("blast_skipped_deep_dark"); return; }

  // Every eligible creeper blast leaves a visible seed on the closest valid surface.
  // The previous 10%-per-block microscopic-only route could legitimately leave no
  // visible colony at all, then wait up to 60 seconds before even showing stage 0.
  const visibleCap = Math.min(cfg.maxPlacementsPerBlast, charged ? 2 : 1);
  let placed = seedVisibleFromBlast(dim, loc, radius, srcStrain, biome, cfg, visibleCap);
  if (placed > 0) diag("blast_visible_seeded", { placed, charged, sourceStrain: srcStrain });
  else diag("blast_no_valid_surface", { radius, charged, x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) });

  // candidate offsets: random pre-filter first so we only look up a handful of blocks
  const cands = [];
  const r2 = radius * radius;
  for (let x = -radius; x <= radius; x++) for (let y = -radius; y <= radius; y++) for (let z = -radius; z <= radius; z++) {
    if (x * x + y * y + z * z <= r2 && Math.random() < cfg.depositChance) cands.push([x, y, z]);
  }
  for (let i = cands.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [cands[i], cands[j]] = [cands[j], cands[i]]; }

  for (const [x, y, z] of cands) {
    if (placed >= cfg.maxPlacementsPerBlast) break;
    const block = getBlockSafe(dim, { x: Math.floor(loc.x) + x, y: Math.floor(loc.y) + y, z: Math.floor(loc.z) + z });
    if (!block || !isFree(block)) continue;
    const below = belowOf(block);
    if (!hasSupport(below)) continue;
    if (cfg.barriersEnabled && blockedBetween(dim, loc, block.location)) continue;
    let inWater = false;
    try { inWater = block.typeId === "minecraft:water" || block.isWaterlogged === true; } catch { /* ignore */ }
    const strain = pickStrain({ below: below.typeId, dim: dim.id, biome, y: block.y, inWater }, srcStrain, cfg.mutationChance, Math.random, cfg.mutationOutcomes);
    if (addPending(dim, block.location, strain)) placed++;
  }
}

function blastOffsets(radius) {
  const r = Math.max(1, Math.min(16, Math.floor(radius))), r2 = r * r;
  const offsets = [];
  for (let x = -r; x <= r; x++) for (let y = -r; y <= r; y++) for (let z = -r; z <= r; z++) {
    const d2 = x * x + y * y + z * z;
    if (d2 <= r2) offsets.push({ x, y, z, d2 });
  }
  // Search close, ground-adjacent cells first; for equal distances prefer lower cells.
  offsets.sort((a, b) => a.d2 - b.d2 || a.y - b.y || a.x - b.x || a.z - b.z);
  return offsets;
}

function seedVisibleFromBlast(dim, loc, radius, srcStrain, biome, cfg, wanted) {
  if (wanted < 1) return 0;
  let placed = 0;
  const origin = { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) };
  for (const off of blastOffsets(radius)) {
    if (placed >= wanted) break;
    const pos = { x: origin.x + off.x, y: origin.y + off.y, z: origin.z + off.z };
    const block = getBlockSafe(dim, pos);
    if (!block || !isFree(block) || !hasSupport(belowOf(block))) continue;
    if (inZone(dim.id, pos)) continue;
    if (cfg.barriersEnabled && blockedBetween(dim, loc, block.location)) continue;
    let inWater = false;
    try { inWater = block.typeId === "minecraft:water" || block.isWaterlogged === true; } catch { /* ignore */ }
    const strain = pickStrain({ below: belowOf(block)?.typeId, dim: dim.id, biome, y: block.y, inWater }, srcStrain, cfg.mutationChance, Math.random, cfg.mutationOutcomes);
    // Stage 2 is still a very small 4x5x4 model. Start explosions at the larger,
    // clearly raised stage 3; normal germination and the stage-4 mutation checkpoint remain intact.
    try { germinate(block, strain, 3); placed++; } catch (e) { diag("blast_seed_write_failed", { x: pos.x, y: pos.y, z: pos.z, err: String(e).slice(0, 80) }); }
  }
  return placed;
}

function applyEffect(dim, loc, eff) {
  let list = [];
  try { list = dim.getEntities({ location: loc, maxDistance: eff.radius }); } catch { return; }
  let n = 0;
  for (const e of list) {
    if (n >= 30) break;
    try {
      if (!e.hasComponent("minecraft:health")) continue;
      if (e.typeId === "minecraft:player" && !isSurvivalLike(e)) continue;
      if (e.typeId === "minecraft:player" && armorBlocksEffect(e, eff.name)) continue; // per-piece Spore-Proof ability
      if (e.getEffect(eff.name)) continue;                    // no duplicate stacking on one entity
      e.addEffect(eff.name, eff.ticks, { amplifier: eff.amp });
      n++;
    } catch { /* invalid entity or unknown effect id: skip */ }
  }
}
