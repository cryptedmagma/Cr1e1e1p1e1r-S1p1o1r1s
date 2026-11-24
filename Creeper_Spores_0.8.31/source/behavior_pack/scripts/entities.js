import { world, system } from "@minecraft/server";
import { VARIANTS } from "./generated_data.js";
import { getConfig } from "./config.js";
import { diag } from "./diag.js";

// Variants that have a switchable special-movement component group, keyed by entity id.
const MOVERS = {};
for (const v of Object.values(VARIANTS)) if (v.move) MOVERS[v.id] = v.move;
const SWITCH = { water: "waterMovement", lava: "lavaMovement", phantom: "phantomMovement" };

function wanted(typeId) {
  const mode = MOVERS[typeId];
  return mode ? getConfig()[SWITCH[mode]] === true : undefined;
}

/** Applies the current feature switch to one entity. Idempotent: group add/remove is a no-op if already in that state. */
export function applyMovement(entity) {
  try {
    const want = wanted(entity.typeId);
    if (want === undefined) return false;
    entity.triggerEvent(want ? "cookiedookie:special_move_on" : "cookiedookie:special_move_off");
    return true;
  } catch (e) {
    diag("movement_event_failed", { type: entity?.typeId, err: String(e).slice(0, 80) });
    return false;
  }
}

/** Re-applies switches to every loaded special-movement creeper (called after settings change). Bounded. */
export function reapplyMovementSwitches() {
  let n = 0;
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let list = [];
    try { list = world.getDimension(dimId).getEntities({ families: ["cs_spore_creeper"] }); } catch { continue; }
    for (const e of list) { if (n >= 200) return n; try { if (applyMovement(e)) n++; } catch { /* removed */ } }
  }
  return n;
}

// First-spawn initialisation (spawn eggs, /summon, hatching). Replay-protected so a reload never re-runs it.
world.afterEvents.entitySpawn.subscribe(({ entity }) => {
  try {
    if (!entity || !MOVERS[entity.typeId]) return;
    if (entity.getDynamicProperty("cs:init") === true) return;
    entity.setDynamicProperty("cs:init", true);
    applyMovement(entity);
  } catch { /* entity already removed */ }
});

// Movement component groups are not a reliable saved-state boundary across chunk unloads.
// Re-apply the current switch whenever a special creeper is loaded back into a chunk.
// The event is optional on older Script API builds; normal spawning still works there.
try {
  world.afterEvents.entityLoad?.subscribe(({ entity }) => {
    try { if (entity && MOVERS[entity.typeId]) applyMovement(entity); }
    catch { /* entity became invalid during the load callback */ }
  });
} catch { /* entityLoad is absent in older Script API builds */ }
