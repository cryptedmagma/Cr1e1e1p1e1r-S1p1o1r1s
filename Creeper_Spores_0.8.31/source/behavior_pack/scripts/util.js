import { world, ItemStack } from "@minecraft/server";

export const NS = "cookiedookie";
export const SPORE_BLOCK = `${NS}:creeper_spores`;
export const STATE_AGE = `${NS}:age`;
export const STATE_ROT = `${NS}:rotation`;
export const STATE_STRAIN = `${NS}:strain`;
export const MAX_AGE = 7;

export const randRot = () => (Math.floor(Math.random() * 4) * 90).toString();
export const randInt = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

/** Read the block containing a world position; floor coordinates consistently, including negatives. */
export function getBlockSafe(dim, loc) {
  try {
    const cell = { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) };
    return dim.getBlock(cell) ?? undefined;
  } catch { return undefined; }
}
export function belowOf(b) { try { return b.below(); } catch { return undefined; } }
export function aboveOf(b) { try { return b.above(); } catch { return undefined; } }

export function isFree(b) {
  try { return !!b && (b.isAir || b.typeId === "minecraft:water"); } catch { return false; }
}
export function isSpore(b) {
  try { return !!b && b.typeId === SPORE_BLOCK; } catch { return false; }
}

/** Surfaces named by the specification. Natural establishment prefers these. */
export const SURFACES = new Set([
  "minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:dirt_with_roots",
  "minecraft:mud", "minecraft:muddy_mangrove_roots", "minecraft:moss_block", "minecraft:podzol",
  "minecraft:mycelium", "minecraft:farmland", "minecraft:sand", "minecraft:red_sand", "minecraft:gravel",
  "minecraft:clay", "minecraft:stone", "minecraft:deepslate", "minecraft:netherrack", "minecraft:soul_soil",
  "minecraft:end_stone", "minecraft:sculk",
]);

/**
 * Support check. Any solid block still counts (so spores already growing on cobblestone,
 * planks etc. in existing worlds are not deleted); spec surfaces such as farmland that
 * are not "solid" are also accepted.
 */
export function hasSupport(below) {
  try { return !!below && (below.isSolid || SURFACES.has(below.typeId)); } catch { return false; }
}

// ---- containment barriers -------------------------------------------------
const BARRIER_EXACT = new Set([
  "minecraft:obsidian", "minecraft:crying_obsidian", "minecraft:iron_bars", "minecraft:tinted_glass",
  "minecraft:glass", "minecraft:glass_pane", "minecraft:fence", "minecraft:reinforced_deepslate",
]);
export function isBarrier(block) {
  try {
    const id = block.typeId;
    if (BARRIER_EXACT.has(id)) return true;
    if (id.endsWith("_stained_glass") || id.endsWith("_stained_glass_pane")) return true;
    if (id.endsWith("_fence") || id.endsWith("_wall")) return true;
    if (id.endsWith("_fence_gate")) return block.permutation.getState("open_bit") !== true; // open gates leak
    return false;
  } catch { return false; }
}

/** Samples the straight segment between two points; true if a real barrier block is crossed. */
export function blockedBetween(dim, from, to, maxSamples = 12) {
  const dx = to.x - from.x, dy = to.y - from.y, dz = to.z - from.z;
  const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const n = Math.min(maxSamples, Math.ceil(dist));
  for (let i = 1; i < n; i++) {
    const t = i / n;
    const b = getBlockSafe(dim, { x: Math.floor(from.x + dx * t), y: Math.floor(from.y + dy * t), z: Math.floor(from.z + dz * t) });
    if (b && isBarrier(b)) return true;
  }
  return false;
}

export function getBiomeId(dim, loc) {
  try {
    if (typeof dim.getBiome === "function") { const b = dim.getBiome(loc); return b?.id ?? b?.toString?.(); }
  } catch { /* API not available in this engine build */ }
  return undefined;
}

export function isCreative(player) { try { return String(player.getGameMode()).toLowerCase() === "creative"; } catch { return false; } }
export function isSurvivalLike(player) {
  try { const g = String(player.getGameMode()).toLowerCase(); return g === "survival" || g === "adventure"; } catch { return true; }
}

export function playSound(dim, id, loc, pitchBase = 0.8) {
  try { dim.playSound(id, loc, { pitch: Math.random() * 0.2 + pitchBase, volume: 1.0 }); } catch { /* audio never decides gameplay */ }
}

/** Awards items; anything that doesn't fit is dropped at the player's feet (no silent loss). */
export function giveItem(player, typeId, amount) {
  amount = Math.floor(amount);
  while (amount > 0) {
    const n = Math.min(amount, 64);
    amount -= n;
    try {
      const stack = new ItemStack(typeId, n);
      const inv = player.getComponent("inventory")?.container;
      const left = inv ? inv.addItem(stack) : stack;
      if (left) player.dimension.spawnItem(left, player.location);
    } catch { /* invalid item id: nothing to award */ }
  }
}

/** Randomised rounding so fractional yield multipliers still average out. */
export function scaledCount(base, mult) {
  const v = base * mult;
  const whole = Math.floor(v);
  return whole + (Math.random() < v - whole ? 1 : 0);
}

const tickLocks = new Map();
/** One transaction per (key, tick): guards against duplicate callbacks within one tick. */
export function lockOnce(key, tick) {
  if (tickLocks.get(key) === tick) return false;
  tickLocks.set(key, tick);
  if (tickLocks.size > 256) { for (const k of tickLocks.keys()) { tickLocks.delete(k); break; } }
  return true;
}

export function playersNear(dim, loc, r) {
  try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch { return []; }
}

export function sendActionBar(player, text) {
  try { player.onScreenDisplay.setActionBar(text); } catch { /* cosmetic */ }
}

/** Enchantment level on an item stack (0 if none / API unavailable). */
export function enchantLevel(item, id) {
  try {
    const e = item?.getComponent("minecraft:enchantable");
    if (!e) return 0;
    const list = e.getEnchantments?.() ?? [];
    for (const en of list) if (String(en.type?.id ?? en.type).replace("minecraft:", "") === id) return en.level | 0;
  } catch { /* unsupported */ }
  return 0;
}
