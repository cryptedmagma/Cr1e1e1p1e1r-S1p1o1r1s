// Pure decision logic (no Minecraft imports) so it can be unit-tested under plain Node.
import { STRAINS, VARIANTS } from "./generated_data.js";

export const STRAIN_INDEX = Object.fromEntries(STRAINS.map((s, i) => [s.key, i]));

const has = (s, ...needles) => typeof s === "string" && needles.some(n => s.includes(n));

/**
 * Chooses the strain for a newly deposited spore.
 * env: { below, dim, biome, y, inWater, nearIds }
 */
export function pickStrain(env, sourceStrain, mutationChance, rng = Math.random, mask = 126) {
  if (sourceStrain > 0 && rng() < 0.6) return sourceStrain;     // strain retention from the source
  if (rng() >= mutationChance) return 0;
  const { below = "", dim = "", biome, y = 64, inWater } = env;
  let pick = 0;
  if (has(dim, "nether")) pick = STRAIN_INDEX.ember;
  else if (has(dim, "the_end")) pick = STRAIN_INDEX.luminous;
  else if (below === "minecraft:sculk") pick = STRAIN_INDEX.sculk;
  else if (inWater) pick = STRAIN_INDEX.aqua;
  else if (has(below, "snow", "ice") || has(biome, "snow", "frozen", "ice", "cold")) pick = STRAIN_INDEX.frost;
  else if (below === "minecraft:mud" || below === "minecraft:muddy_mangrove_roots" || has(biome, "swamp", "mangrove")) pick = STRAIN_INDEX.toxic;
  else if (y < 0) pick = STRAIN_INDEX.luminous;
  return allowed(pick, mask) ? pick : 0;       // a disabled outcome means "no mutation", never a substitute
}

export function allowed(strain, mask) { return strain > 0 && ((mask >> strain) & 1) === 1; }

/** Environment-driven mutation for an existing pod at its mid-life milestone. */
export function pickMutation(nearIds, mask = 126) {
  const m = pickMutationRaw(nearIds);
  return allowed(m, mask) ? m : -1;
}
function pickMutationRaw(nearIds) {
  const t = nearIds.join("|");
  if (has(t, "glowstone", "shroomlight", "sea_lantern")) return STRAIN_INDEX.luminous;
  if (has(t, "magma", "lava", "fire")) return STRAIN_INDEX.ember;
  if (has(t, "ice", "snow")) return STRAIN_INDEX.frost;
  if (has(t, "water", "kelp", "seagrass")) return STRAIN_INDEX.aqua;
  if (has(t, "sculk")) return STRAIN_INDEX.sculk;
  if (has(t, "minecraft:mud")) return STRAIN_INDEX.toxic;
  return -1;
}

/**
 * Chooses the creeper that hatches. Returns a key of VARIANTS or null for the vanilla creeper.
 * env: { strain, below, dim, biome, y, inWater }
 */
export function pickVariant(env, variantChance, rng = Math.random) {
  const { strain = 0, below = "", dim = "", biome, y = 64, inWater, nearIds = [] } = env;
  const S = STRAIN_INDEX;
  let key = null;
  if (strain === S.royal) key = rng() < 0.35 ? "spore_queen" : "moss";
  else if (strain === S.luminous) key = (y < -30 && rng() < 0.4) ? "crystal" : "glowing";
  else if (strain === S.toxic) key = (has(biome, "jungle", "bamboo") || rng() < 0.3) ? "thorn" : "swamp";
  else if (strain === S.frost) key = "snow";
  else if (strain === S.ember) key = (has(dim, "nether") && rng() < 0.3) ? "lava" : "nether";
  else if (strain === S.aqua) key = "water";
  else if (strain === S.sculk) key = (has(biome, "pale_garden") || rng() < 0.2) ? "phantom" : "sculk";
  else {
    if (rng() >= variantChance) return rare(rng);
    // Source-driven 0.6.0 variants: restricted to common spores and their matching ecology.
    // Retain existing 0.5.0 logic as the fallback; these may still be overridden by rare() below.
    if (nearIds.some(id => has(id, "_log", "_stem")) && has(biome, "forest", "taiga") && rng() < 0.45) key = "carved_wood";
    else if (has(biome, "bamboo") && rng() < 0.50) key = "slender_green";
    else if (below === "minecraft:grass_block" && has(biome, "plains", "meadow") && rng() < 0.35) key = "grass_crown";
    else if (has(dim, "nether")) key = "nether";
    else if (has(dim, "the_end")) key = "end";
    else if (below === "minecraft:sculk") key = "sculk";
    else if (below === "minecraft:mycelium" || has(biome, "mushroom")) key = "mushroom";
    else if (inWater) key = "water";
    else if (has(biome, "pale_garden")) key = "phantom";
    else if (below === "minecraft:moss_block" || has(biome, "lush")) key = "moss";
    else if (below === "minecraft:sand" || below === "minecraft:red_sand" || has(biome, "desert", "badlands", "mesa")) key = "desert";
    else if (below === "minecraft:mud" || has(biome, "swamp", "mangrove")) key = "swamp";
    else if (has(biome, "jungle", "bamboo")) key = "jungle";
    else if (has(biome, "snow", "frozen", "ice", "cold")) key = "snow";
    else if (has(biome, "cherry", "flower", "sunflower")) key = "flower";
    else if ((below === "minecraft:stone" || below === "minecraft:deepslate") && y < 50) key = (y < -30 && rng() < 0.3) ? "crystal" : "cave";
    else key = null;
  }
  return rare(rng, key);
}

function rare(rng, key = null) {
  const r = rng();
  if (r < 0.03) return "giant";
  if (r < 0.09) return "miniature";
  return key;
}

export function variantFromTypeId(typeId) {
  if (typeId === "minecraft:creeper") return { key: null, def: null };
  for (const [key, def] of Object.entries(VARIANTS)) if (def.id === typeId) return { key, def };
  return undefined;
}
