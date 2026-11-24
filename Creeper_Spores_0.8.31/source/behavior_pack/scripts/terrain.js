// Creeper Spores 0.4.0 — reversible infection of a conservative whitelist of terrain blocks.
// Original permutations are stored BEFORE replacement. This never targets chests, machines,
// portals or blocks with inventories. Native stone/dirt cannot reveal whether a player placed it;
// infection is opt-in so existing builds are not silently altered.
import { world, system, BlockPermutation, ItemStack } from "@minecraft/server";
import { podHooks } from "./spores.js";
import { getConfig } from "./config.js";
import { NS, getBlockSafe, isSpore, sendActionBar } from "./util.js";
import { diag } from "./diag.js";
import { knownPlayerPlaced } from "./placed_block_guard.js";
const ORNAMENTAL = new Set(["oak_log", "spruce_log", "birch_log", "oak_leaves", "oak_planks", "spruce_planks", "birch_planks", "white_wool", "white_concrete", "glass", "ice", "snow", "snow_block"]);
const TYPES = new Set(["grass_block", "dirt", "coarse_dirt", "stone", "deepslate", "cobblestone", "sand", "red_sand", "clay", "moss_block", "mud", "netherrack", "soul_soil"]);
const PREFIX = "cs:infect:";
const key = (dim, p) => `${PREFIX}${dim.id}:${p.x},${p.y},${p.z}`;
const marked = new Set();
let scanned = false;
function initMarked() {
  if (scanned) return;
  scanned = true;
  try { for (const k of world.getDynamicPropertyIds()) if (k.startsWith(PREFIX)) marked.add(k); }
  catch { scanned = false; }
}
const locOf = p => ({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) });
function stored(dim, p) { try { const x = world.getDynamicProperty(key(dim,p)); return typeof x === "string" ? JSON.parse(x) : null; } catch { return null; } }
function remember(dim,p,b) {
  try {
    const states = b.permutation.getAllStates?.() ?? {};
    world.setDynamicProperty(key(dim,p), JSON.stringify({ type: b.typeId, states }));
    marked.add(key(dim,p));
    return true;
  } catch { diag("infection_store_failed"); return false; }
}
function forget(dim,p) { try { world.setDynamicProperty(key(dim,p),undefined); } catch {} marked.delete(key(dim,p)); }
export function cure(dim, p) {
  p = locOf(p);
  const b = getBlockSafe(dim, p);
  if (!b || !b.typeId.startsWith(`${NS}:infected_`)) return false;
  const rec = stored(dim,p);
  if (!rec || typeof rec.type !== "string" || !rec.type.startsWith("minecraft:")) { diag("infection_missing_original"); return false; }
  try {
    b.setPermutation(BlockPermutation.resolve(rec.type, rec.states ?? {}));
    forget(dim,p); return true;
  } catch {
    try { b.setType(rec.type); forget(dim,p); return true; } catch { return false; }
  }
}
export function cureNear(dim, center, radius = 4, max = 36) {
  let n = 0; const p = locOf(center);
  for (let dx=-radius;dx<=radius && n<max;dx++) for (let dz=-radius;dz<=radius && n<max;dz++) for (let dy=-2;dy<=2 && n<max;dy++) {
    if (cure(dim,{x:p.x+dx,y:p.y+dy,z:p.z+dz})) n++;
  }
  return n;
}
function infectNear(block, cfg) {
  if (!cfg.terrainInfection || Math.random() > cfg.infectionChance) return;
  initMarked();
  const dim=block.dimension, sx=block.x+(Math.floor(Math.random()*5)-2), sz=block.z+(Math.floor(Math.random()*5)-2);
  const y=block.y-1 + Math.floor(Math.random()*3);
  const p={x:sx,y,z:sz};
  if (marked.size > 1800) { diag("infection_cap_reached"); return; }
  const b=getBlockSafe(dim,p); if (!b || !b.typeId.startsWith("minecraft:")) return;
  const name=b.typeId.slice(10);
  if ((!TYPES.has(name) && !(cfg.ornamentalInfection && ORNAMENTAL.has(name))) || stored(dim,p)) return;
  if (knownPlayerPlaced(dim.id,p)) {diag("infection_player_placed_guard");return;}
  // Do not consume the supporting block of an existing pod.
  if (isSpore(getBlockSafe(dim,{x:p.x,y:p.y+1,z:p.z}))) return;
  if (!remember(dim,p,b)) return;
  try { b.setType(`${NS}:infected_${name}`); } catch { forget(dim,p); diag("infection_replace_failed"); }
}
podHooks.push((block,age,strain,cfg)=>{ if (age >= 5) infectNear(block,cfg); });

// A purifier can reverse nearby infections without replacing its existing spore-removal behavior.
world.afterEvents.playerBreakBlock.subscribe(({ block, brokenBlockPermutation, player })=>{
  try {
    if (!brokenBlockPermutation?.type?.id?.startsWith(`${NS}:infected_`)) return;
    const rec=stored(block.dimension,block.location);
    if (!rec) return;
    forget(block.dimension,block.location);
    if (String(player?.getGameMode?.()).toLowerCase() === "creative") return;
    try { block.dimension.spawnItem(new ItemStack(rec.type,1),{x:block.x+0.5,y:block.y+0.5,z:block.z+0.5}); } catch {}
  } catch {}
});
// Brush + infected block: restore the original terrain, not a random neighboring material.
world.beforeEvents.playerInteractWithBlock.subscribe(ev=>{
  try {
    if (!ev.block?.typeId?.startsWith(`${NS}:infected_`)) return;
    const id=ev.itemStack?.typeId;
    if (id!=="minecraft:brush") return;
    ev.cancel=true;
    const dim=ev.block.dimension,p={...ev.block.location},player=ev.player;
    system.run(()=>{ if(cure(dim,p)) sendActionBar(player,"§aInfected terrain restored."); });
  } catch {}
});
