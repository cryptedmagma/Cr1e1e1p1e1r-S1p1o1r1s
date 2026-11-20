import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";

// Quarantine / suppression zones (sprayer item). Stored as one JSON world property so they survive reloads.
// A zone suppresses NEW spore placement and hatching inside its radius until it expires; it never deletes existing growths.
const KEY = "cs:zones";
const MAX_ZONES = 32;
let zones = null;

function load() {
  if (zones) return;
  zones = [];
  try {
    const raw = world.getDynamicProperty(KEY);
    if (typeof raw === "string") {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) zones = arr.filter(z => z && typeof z.d === "string" && [z.x, z.y, z.z, z.r, z.e].every(Number.isFinite));
    }
  } catch { zones = []; }
}
function save() { try { world.setDynamicProperty(KEY, JSON.stringify(zones)); } catch { /* keep in-memory copy */ } }
function prune() { const now = world.getAbsoluteTime(); const n = zones.length; zones = zones.filter(z => z.e > now); if (zones.length !== n) save(); }

/** durationTicks of real world time; replaces the oldest zone when full. Returns the zone or null. */
export function addZone(dimId, loc, radius, durationTicks) {
  load(); prune();
  const fx = Math.floor(loc.x), fy = Math.floor(loc.y), fz = Math.floor(loc.z);
  const same = zones.find(q => q.d === dimId && q.x === fx && q.y === fy && q.z === fz && q.r === radius);
  if (same) { same.e = Math.max(same.e, world.getAbsoluteTime() + durationTicks); save(); return same; }   // refresh, don't duplicate
  if (zones.length >= MAX_ZONES) zones.shift();
  const z = { d: dimId, x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z), r: radius, e: world.getAbsoluteTime() + durationTicks };
  zones.push(z); save();
  return z;
}

/** True if a point in this dimension is inside an active zone. Cheap: at most MAX_ZONES comparisons. */
export function inZone(dimId, loc) {
  if (!getConfig().zonesEnabled) return false;
  load();
  if (!zones.length) return false;
  const now = world.getAbsoluteTime();
  for (const z of zones) {
    if (z.e <= now || z.d !== dimId) continue;
    const dx = loc.x - z.x, dy = loc.y - z.y, dz = loc.z - z.z;
    if (dx * dx + dy * dy + dz * dz <= z.r * z.r) return true;
  }
  return false;
}

export function zoneCount() { load(); prune(); return zones.length; }
export function _resetForTests() { zones = null; }
