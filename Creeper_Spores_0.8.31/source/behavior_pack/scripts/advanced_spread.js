// Creeper Spores 0.4.0 — bounded, independently gated transmission routes.
// No visual effect controls placement; routes are separate and share placement validation.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBlockSafe, belowOf, isFree, hasSupport, isSpore, blockedBetween, getBiomeId } from "./util.js";
import { addPending, podHooks } from "./spores.js";
import { inZone } from "./zones.js";
import { diag } from "./diag.js";
import { waterRoute } from "./water_flow.js";

const routes = [
  ["waterTransport", "water"], ["rainTransport", "rain"], ["windTransport", "wind"],
  ["vineTransport", "vine"], ["leafTransport", "leaf"],
  ["caveAirTransport", "cave_air"],
];
const blocksVine = new Set(["minecraft:vine", "minecraft:cave_vines", "minecraft:cave_vines_body_with_berries", "minecraft:weeping_vines", "minecraft:twisting_vines"]);
const leaves = new Set(["minecraft:oak_leaves", "minecraft:birch_leaves", "minecraft:spruce_leaves", "minecraft:jungle_leaves", "minecraft:acacia_leaves", "minecraft:dark_oak_leaves", "minecraft:cherry_leaves", "minecraft:mangrove_leaves"]);
const lastRoute = new Map();
const carriers = new Map();
const key = (dim, p) => `${dim.id}:${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`;
function naturalAllowed(dim, p, cfg) {
  if (cfg.deepDarkBlocksNatural) {
    const biome = getBiomeId(dim, p);
    if (typeof biome === "string" && biome.includes("deep_dark")) return false;
  }
  return !inZone(dim.id, p);
}
function routeDeposit(dim, from, target, strain, cfg) {
  if (!naturalAllowed(dim, target, cfg)) return false;
  const b = getBlockSafe(dim, target);
  if (!b || !isFree(b) || !hasSupport(belowOf(b))) return false;
  if (cfg.barriersEnabled && blockedBetween(dim, from, target)) return false;
  return !!addPending(dim, b.location, strain);
}
function attemptRoute(b, strain, cfg, route) {
  const dim = b.dimension, p = b.location, under = belowOf(b);
  const above = getBlockSafe(dim, { x: p.x, y: p.y + 1, z: p.z });
  let dx = 0, dz = 0, dy = 0;
  if (route === "water") {
    const flow=cfg.waterCurrentRouting ? waterRoute(dim,p) : null;
    if(flow) { dx=flow.x-p.x; dz=flow.z-p.z; dy=flow.y-p.y; }
    else {
      const w = [[1,0],[-1,0],[0,1],[0,-1]].filter(([x,z]) => getBlockSafe(dim,{x:p.x+x,y:p.y,z:p.z+z})?.typeId === "minecraft:water");
      if (!w.length) return;
      [dx,dz]=w[Math.floor(Math.random()*w.length)]; // one-cell fallback, never jump 4 across walls
    }
  } else if (route === "rain") {
    let raining = false;
    try { const t = String(dim.getWeather?.() ?? "").toLowerCase(); raining = t.includes("rain") || t.includes("thunder"); } catch {}
    if (!raining || !under || !under.isSolid) return;
    dx = Math.random() < 0.5 ? -2 : 2; dz = Math.random() < 0.5 ? -1 : 1;
  } else if (route === "wind") {
    if (above && !isFree(above)) return;
    dx = (Math.floor(world.getAbsoluteTime()/2400) % 3) - 1;
    dz = ((Math.floor(world.getAbsoluteTime()/1300) + 1) % 3) - 1;
    if (!dx && !dz) dx = 1;
    dx *= 3; dz *= 3;
  } else if (route === "vine") {
    if (!blocksVine.has(above?.typeId) && !blocksVine.has(under?.typeId)) return;
    dy = Math.random() < 0.5 ? -1 : 1;
    dx = Math.random() < 0.5 ? 1 : -1;
  } else if (route === "leaf") {
    if (!leaves.has(above?.typeId)) return;
    dx = Math.random() < 0.5 ? 1 : -1;
    dz = Math.random() < 0.5 ? 1 : -1;
  } else if (route === "cave_air") {
    // Explicit opt-in approximation: requires open air under a solid ceiling.
    // It never assumes weather or a nonexistent Bedrock wind vector.
    const ceiling = getBlockSafe(dim,{x:p.x,y:p.y+2,z:p.z});
    if (!above?.isAir || !ceiling?.isSolid) return;
    dx = [-2,-1,1,2][Math.floor(Math.random()*4)];
    dz = [-2,-1,1,2][Math.floor(Math.random()*4)];
  }
  const dest = { x: p.x + dx, y: p.y + dy, z: p.z + dz };
  if (routeDeposit(dim, p, dest, strain, cfg)) diag(`transport_${route}_ok`);
}
// Each pod may attempt at most ONE route per random-tick callback, with a per-source cooldown.
podHooks.push((block, age, strain, cfg) => {
  if (age < 5 || !cfg.advancedTransport) return;
  const k = key(block.dimension, block.location), now = system.currentTick;
  if ((lastRoute.get(k) ?? -99999) + 60 > now) return;
  const active = routes.filter(([switchName]) => cfg[switchName]);
  if (!active.length || Math.random() > cfg.transportChance) return;
  lastRoute.set(k, now);
  const r = active[Math.floor(Math.random()*active.length)][1];
  attemptRoute(block, strain, cfg, r);
  if (lastRoute.size > 4096) lastRoute.clear();
});

// Boats, minecarts, and dropped items can carry a finite number of spore deposits.
// This is a local scan around players only: never enumerate all entities in a dimension.
system.runInterval(() => {
  const cfg = getConfig();
  if (!cfg.advancedTransport || !cfg.vehicleTransport && !cfg.itemTransport) { carriers.clear(); return; }
  const now = system.currentTick, visited = new Set();
  for (const player of world.getPlayers()) {
    let entities = [];
    try { entities = player.dimension.getEntities({ location: player.location, maxDistance: 24 }); } catch { continue; }
    let count = 0;
    for (const e of entities) {
      if (++count > 36) break;
      if (visited.has(e.id)) continue; visited.add(e.id);
      const id = e.typeId;
      const isVehicle = id.includes("boat") || id.includes("minecart");
      const isItem = id === "minecraft:item";
      if (!(isVehicle && cfg.vehicleTransport || isItem && cfg.itemTransport)) continue;
      try {
        const p = e.location, dim = e.dimension;
        const stand = getBlockSafe(dim, { x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) });
        let c = carriers.get(e.id);
        if (isSpore(stand) && stand.permutation.getState("cookiedookie:age") >= 3) {
          c = { strain: stand.permutation.getState("cookiedookie:strain") ?? 0, remain: 3, until: now + 1800 };
          carriers.set(e.id, c);
        }
        if (!c) continue;
        if (now > c.until || c.remain <= 0) { carriers.delete(e.id); continue; }
        if (Math.random() < cfg.transportChance && routeDeposit(dim, p, p, c.strain, cfg)) c.remain--;
      } catch { carriers.delete(e.id); }
    }
  }
  if (carriers.size > 500) carriers.clear();
}, 80);

// Portals preserve an already-carried player's strain, not an uncontrolled dimension-wide infection.
const portalCarry = new Map();
// Remote carrier records expire without loading or forcing extra chunks.
try { world.afterEvents.playerDimensionChange?.subscribe(({ player }) => {
  const cfg = getConfig(); if (!cfg.portalTransport || !cfg.advancedTransport) return;
  if (!player?.id) return;
  const strain = player.getDynamicProperty?.("cs:carried_strain");
  if (typeof strain !== "number" || strain < 0 || strain > 7) return;
  portalCarry.set(player.id, { strain, expires: system.currentTick + 120 });
}); } catch { /* event unavailable: no portal transmission */ }
system.runInterval(() => {
  const cfg = getConfig();
  for (const p of world.getPlayers()) {
    const c = portalCarry.get(p.id);
    if (!c) continue;
    portalCarry.delete(p.id);
    if (!cfg.portalTransport || system.currentTick > c.expires) continue;
    try {
      const at = getBlockSafe(p.dimension, p.location);
      if (isSpore(at)) continue;
      if (Math.random() < cfg.transportChance) routeDeposit(p.dimension, p.location, p.location, c.strain, cfg);
    } catch {}
  }
}, 40);
