import { world } from "@minecraft/server";

const KEY = "cs:config";

export const DEFAULTS = {
  hatchEnabled: true,
  depositChance: 0.10,          // per eligible block, per blast (original value)
  radiusNormal: 4,              // original value
  radiusCharged: 7,             // original value
  maxPlacementsPerBlast: 24,    // bounded per-event workload
  germinationMinTicks: 20,      // 1 second minimum delay before a microscopic deposit appears
  germinationMaxTicks: 100,     // 5 second maximum default delay
  growthAdvanceChance: 1.0,     // multiplies the block's random tick; can only slow growth (tick range is fixed in the block JSON)
  maxPendingSpores: 4000,
  mutationChance: 0.10,
  variantChance: 0.35,          // chance a common-strain pod hatches a variant instead of a vanilla creeper
  maxCreepersNear: 8,           // hatching is deferred while this many creepers are within 24 blocks
  harvestYield: 1.0,
  barriersEnabled: true,
  carriersEnabled: true,
  carrierChance: 0.15,
  mobDropOnce: true,          // final deposit cleans the mob; early drip does not
  mobPickupAge: 1,           // collect from stage 1 or older when stepping on it
  mobMinTravelBlocks: 20,   // final drop needs 20 walked blocks and 40 ticks
  mobMinCarryTicks: 40,
  mobDripTravelBlocks: 15,  // one 40% early drip roll, without cleaning
  mobDripChance: 0.40,
  mobPickupImmunityTicks: 200, // prevent instant re-infection after a successful drop
  infectionVisuals: true,         // lightweight cosmetic carrier cues; no replacement skins or bud
  infectionVisualQuality: 1,      // 0 off, 1 light (default), 2 fuller
  infectionVisualRange: 24,       // only emit for players nearby
  shedChance: 0.05,
  deepDarkBlocksNatural: true,
  // --- milestone 0.2 feature switches (each independent and reversible) ---
  waterMovement: true,          // water creeper swims
  lavaMovement: true,           // lava creeper walks through lava
  phantomMovement: true,        // phantom creeper hovers/flies
  hatchAnimation: true,         // shake -> open -> emerge sequence before the creeper appears
  emergenceStages: true,        // newborn grows through two small stages
  debugDiagnostics: true,       // keep a ring buffer of rejection reasons (counters are always kept)
  // --- 0.3.0 ---
  spreadEnabled: true,          // mature pods seed neighbours (colony growth)
  spreadChance: 0.04,           // per random tick of a mature (age>=5) pod
  colonySize: 12,               // max pods within 4 blocks of a spread source
  cropEcology: true,            // pods affect adjacent crops
  mobEcology: true,             // mobs trample young pods / carry spores
  redstoneControllers: true,
  controllerCooldown: 40,       // ticks between controller actions
  zonesEnabled: true,           // quarantine/suppression zones are honoured
  mutationOutcomes: 126,        // bitmask: bit n allows strain n as a mutation result (1..6; royal is player-made only)
  // 0.8.0 additions: no world changes unless individually enabled.
  colonyNetworks: true,          // read-only connected-colony discovery
  networkCooperation: false,     // opt-in one-stage cooperation in a loaded connected network
  variantEcology: false,         // optional non-combat environment adaptations
  hybridPlants: false,           // opt-in non-destructive hybrid growth and harvesting
  fieldRuins: false,             // opt-in small constructed nests in validated empty space
  // 0.4.0 — independent gates, conservative settings for unverified/destructive systems.
  advancedTransport: true,
  airClouds: true,           // finite particle-only drifting airborne carriers, no extra entities
  airCloudSpawnChance: 0.12,// per selected mature-pod random tick; capped and zone-aware
  airCloudMaxActive: 64,
  airCloudSettleChance: 0.18,
  waterCurrentRouting: true, // prefer actual observed neighbouring liquid levels where supported
  waterTransport: true,
  caveAirTransport: false, // airflow approximation, never actual fluid physics
  splashPotionTransport: false, // explicit opt-in, requires carried strain
  armoredCarrierTransport: false, // explicit opt-in, never gives full armor infection
  ornamentalInfection: false, // extra infected materials, opt in separately
  rainTransport: true,
  windTransport: true,
  vineTransport: true,
  leafTransport: true,
  itemTransport: true,
  vehicleTransport: true,
  portalTransport: true,
  transportChance: 0.04,
  terrainInfection: false,   // requires explicit opt-in: changes vanilla blocks and saves restoration metadata
  infectionChance: 0.04,
  naturalGeneration: false,  // explicit opt-in to add spores to already-existing loaded terrain
  naturalSpawnChance: 0.10,
  traderEncounters: true,
  structureNests: false,     // pre-release getGeneratedStructures is optional; no guessing structures
  plantEcology: true,
  mobReactions: true,
  villagerReactions: true,
  incubatorsEnabled: true,
  incubatorInterval: 200
};

// [min, max] for numeric settings; booleans are listed with null.
export const BOUNDS = {
  colonyNetworks: null,
  networkCooperation: null,
  variantEcology: null,
  hybridPlants: null,
  fieldRuins: null,
  hatchEnabled: null,
  depositChance: [0, 1],
  radiusNormal: [1, 12],
  radiusCharged: [1, 16],
  maxPlacementsPerBlast: [1, 200],
  germinationMinTicks: [20, 24000],
  germinationMaxTicks: [20, 48000],
  growthAdvanceChance: [0.05, 1],
  maxPendingSpores: [100, 20000],
  mutationChance: [0, 1],
  variantChance: [0, 1],
  maxCreepersNear: [1, 64],
  harvestYield: [0, 4],
  barriersEnabled: null,
  carriersEnabled: null,
  carrierChance: [0, 1],
  mobDropOnce: null,
  mobPickupAge: [0, 7],
  mobMinTravelBlocks: [20, 128],
  mobMinCarryTicks: [40, 2400],
  mobDripTravelBlocks: [15, 128],
  mobDripChance: [0, 1],
  mobPickupImmunityTicks: [0, 2400],
  infectionVisuals: null,
  infectionVisualQuality: [0, 2],
  infectionVisualRange: [8, 32],
  shedChance: [0, 1],
  deepDarkBlocksNatural: null,
  waterMovement: null,
  lavaMovement: null,
  phantomMovement: null,
  hatchAnimation: null,
  emergenceStages: null,
  debugDiagnostics: null,
  mutationOutcomes: [0, 126],
  spreadEnabled: null,
  spreadChance: [0, 1],
  colonySize: [1, 64],
  cropEcology: null,
  mobEcology: null,
  redstoneControllers: null,
  controllerCooldown: [10, 1200],
  zonesEnabled: null,
  advancedTransport: null,
  airClouds: null,
  airCloudSpawnChance: [0, 0.4],
  airCloudMaxActive: [8, 96],
  airCloudSettleChance: [0, 1],
  waterCurrentRouting: null,
  waterTransport: null,
  caveAirTransport: null,
  splashPotionTransport: null,
  armoredCarrierTransport: null,
  ornamentalInfection: null,
  rainTransport: null,
  windTransport: null,
  vineTransport: null,
  leafTransport: null,
  itemTransport: null,
  vehicleTransport: null,
  portalTransport: null,
  transportChance: [0, 1],
  terrainInfection: null,
  infectionChance: [0, 0.5],
  naturalGeneration: null,
  naturalSpawnChance: [0, 0.5],
  traderEncounters: null,
  structureNests: null,
  plantEcology: null,
  mobReactions: null,
  villagerReactions: null,
  incubatorsEnabled: null,
  incubatorInterval: [20, 2400],
};
const INTEGERS = new Set(["mutationOutcomes", "infectionVisualQuality", "infectionVisualRange", "airCloudMaxActive"]);

let cache = null;
const REV_KEY = "cs:config_rev";
/** Monotonic revision, bumped on every committed change; forms compare it to detect a concurrent admin edit. */
export function getRev() { try { const r = world.getDynamicProperty(REV_KEY); return typeof r === "number" ? r : 0; } catch { return 0; } }
function bump() { try { world.setDynamicProperty(REV_KEY, getRev() + 1); } catch { /* ignore */ } }

/** Returns a validated value or undefined (never throws). */
function validate(key, value) {
  if (!(key in DEFAULTS)) return undefined;
  const b = BOUNDS[key];
  if (b === null) return typeof value === "boolean" ? value : undefined;
  if (typeof value !== "number" || !Number.isFinite(value)) return undefined;
  const v = Math.min(b[1], Math.max(b[0], value));
  return key === "mutationOutcomes" ? (Math.round(v) & 126) : INTEGERS.has(key) ? Math.round(v) : v;   // mutation mask can only contain strains 1..6
}

export function getConfig() {
  if (cache) return cache;
  const cfg = { ...DEFAULTS };
  try {
    const raw = world.getDynamicProperty(KEY);
    if (typeof raw === "string") {
      const saved = JSON.parse(raw);
      for (const k of Object.keys(DEFAULTS)) { const v = validate(k, saved[k]); if (v !== undefined) cfg[k] = v; }
    }
  } catch { /* corrupt saved config: fall back to defaults */ }
  // Version 0.6.1 stored old defaults (stage=3, distance=2). New rules take precedence;
  // keep user-chosen larger values, but guarantee this release's 1/15/20/40 minimums.
  cfg.mobPickupAge = 1; // age 1 is always eligible under the new rule
  cfg.mobMinTravelBlocks = Math.max(20, cfg.mobMinTravelBlocks);
  cfg.mobMinCarryTicks = Math.max(40, cfg.mobMinCarryTicks);
  cfg.mobDripTravelBlocks = Math.max(15, cfg.mobDripTravelBlocks);
  // Upgrade untouched legacy defaults so propagated spores become visible promptly.
  // A range changed away from the previous defaults is preserved.
  let migratedLegacyGermination = false;
  if (cfg.germinationMinTicks === 100 && cfg.germinationMaxTicks === 1200) {
    cfg.germinationMinTicks = 20;
    cfg.germinationMaxTicks = 100;
    migratedLegacyGermination = true;
  }
  if (migratedLegacyGermination) { try { world.setDynamicProperty(KEY, JSON.stringify(cfg)); } catch { /* migration retries on next load */ } }
  if (cfg.germinationMaxTicks < cfg.germinationMinTicks) cfg.germinationMaxTicks = cfg.germinationMinTicks;
  cache = cfg;
  return cfg;
}

/** Applies a patch atomically: if nothing validates, the last confirmed config is untouched. */
export function setConfig(patch) {
  const next = { ...getConfig() };
  let changed = 0;
  for (const [k, v] of Object.entries(patch)) {
    const ok = validate(k, v);
    if (ok !== undefined) { next[k] = ok; changed++; }
  }
  if (!changed) return false;
  if (next.germinationMaxTicks < next.germinationMinTicks) next.germinationMaxTicks = next.germinationMinTicks;
  try { world.setDynamicProperty(KEY, JSON.stringify(next)); } catch { return false; }
  cache = next;
  bump();
  return true;
}

/** Restore defaults for only the named keys (other saved values untouched). */
export function resetKeys(keys) {
  const patch = {};
  for (const k of keys) if (k in DEFAULTS) patch[k] = DEFAULTS[k];
  return setConfig(patch);
}

export function exportConfig() { return JSON.stringify(getConfig()); }

/** Imports a JSON string produced by exportConfig. Unknown/invalid keys are ignored; returns number applied. */
export function importConfig(text) {
  let obj;
  try { obj = JSON.parse(text); } catch { return 0; }
  if (!obj || typeof obj !== "object") return 0;
  const before = JSON.stringify(getConfig());
  const patch = {};
  for (const k of Object.keys(DEFAULTS)) if (k in obj && validate(k, obj[k]) !== undefined) patch[k] = obj[k];   // invalid values are skipped, not counted
  setConfig(patch);
  return JSON.stringify(getConfig()) === before ? 0 : Object.keys(patch).length;
}

export function resetConfig() {
  try { world.setDynamicProperty(KEY, undefined); } catch { return false; }
  cache = { ...DEFAULTS };
  bump();
  return true;
}

export function isAdmin(player) {
  try { return player.hasTag("cs_admin") || (typeof player.isOp === "function" && player.isOp()); } catch { return false; }
}
