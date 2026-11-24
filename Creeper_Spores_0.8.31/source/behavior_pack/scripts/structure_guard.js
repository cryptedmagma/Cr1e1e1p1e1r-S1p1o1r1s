// Creeper Spores 0.8.31 — shared placement safeguards for generated ruins and structure nests.
// Approved rules: never overwrite containers, crops or existing spore pods, and never place inside a
// quarantine zone. Only empty air cells are ever written.
import { inZone } from "./zones.js";
export const PROTECTED_EXACT = new Set([
  "cookiedookie:creeper_spores",
  "minecraft:wheat", "minecraft:carrots", "minecraft:potatoes", "minecraft:beetroot", "minecraft:melon_stem",
  "minecraft:pumpkin_stem", "minecraft:torchflower_crop", "minecraft:pitcher_crop", "minecraft:sweet_berry_bush",
  "minecraft:cocoa", "minecraft:nether_wart", "minecraft:farmland",
  "minecraft:chest", "minecraft:trapped_chest", "minecraft:barrel", "minecraft:ender_chest", "minecraft:hopper",
  "minecraft:dropper", "minecraft:dispenser", "minecraft:furnace", "minecraft:blast_furnace", "minecraft:smoker",
  "minecraft:brewing_stand", "minecraft:crafter", "minecraft:decorated_pot", "minecraft:chiseled_bookshelf",
  "minecraft:lectern", "minecraft:jukebox", "minecraft:campfire", "minecraft:soul_campfire", "minecraft:beehive",
  "minecraft:bee_nest",
]);
/** Pure rule: may a generated structure block be written into a cell holding this block type? */
export function cellIsProtected(typeId) {
  return typeof typeId !== "string" || PROTECTED_EXACT.has(typeId) || typeId.endsWith("shulker_box");
}
/** Runtime check for one target cell: air only, not protected, not quarantined. */
export function safeStructureCell(dim, block) {
  try {
    if (!block || !block.isAir || cellIsProtected(block.typeId)) return false;
    return !inZone(dim.id, { x: block.x, y: block.y, z: block.z });
  } catch { return false; }
}
