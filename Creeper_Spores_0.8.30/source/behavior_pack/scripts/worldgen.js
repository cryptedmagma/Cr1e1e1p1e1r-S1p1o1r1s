// Creeper Spores 0.4.0 — conservative natural establishment near loaded players.
// Default OFF for upgraded worlds; activating this opts into sparse generation.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBiomeId, SURFACES, getBlockSafe, hasSupport, isFree } from "./util.js";
import { addPending } from "./spores.js";
import { inZone } from "./zones.js";
import { diag } from "./diag.js";
import { biomeMultiplier } from "./tuning.js";
const KEY = "cs:natural_cells_v1";
let cells;
function load() {
  if (cells) return;
  try { const a = JSON.parse(world.getDynamicProperty(KEY) ?? "[]"); cells = new Set(Array.isArray(a) ? a.slice(-2000) : []); } catch { cells = new Set(); }
}
function save() {
  try { world.setDynamicProperty(KEY, JSON.stringify([...cells].slice(-2000))); } catch { diag("worldgen_save_failed"); }
}
const allowedBiome = ["plains", "forest", "taiga", "swamp", "mangrove", "desert", "savanna", "badlands", "jungle", "bamboo", "cherry", "pale_garden", "mushroom", "lush_caves"];
let turn = 0;
system.runInterval(() => {
  const cfg = getConfig();
  if (!cfg.naturalGeneration) return;
  load();
  const players = world.getPlayers(); if (!players.length) return;
  const p = players[turn++ % players.length];
  const dim = p.dimension;
  if (dim.id !== "minecraft:overworld" && dim.id !== "overworld") return;
  const x = (Math.floor(p.location.x/16) + Math.floor(Math.random()*7)-3)*16;
  const z = (Math.floor(p.location.z/16) + Math.floor(Math.random()*7)-3)*16;
  const cx = Math.floor(x/16), cz = Math.floor(z/16), k = `${dim.id}:${cx}:${cz}`;
  if (cells.has(k)) return;
  // Mark a cell as inspected even if it has no eligible ground. An unload will be revisited later.
  let top;
  try { top = dim.getTopmostBlock?.({ x: x + 8, z: z + 8 }); } catch {}
  if (!top) {
    // Bounded fallback for engine builds without the topmost-block API.
    // Scan only locally loaded terrain, never cause chunk loading.
    const yTop = Math.min(319, Math.floor(p.location.y) + 24);
    for (let y=yTop; y>=Math.max(-64,yTop-56); y--) {
      const b=getBlockSafe(dim,{x:x+8,y,z:z+8});
      if(!b)break;
      if(b.isSolid){top=b;break;}
    }
  }
  if (!top) return;
  const loc = { x: x + 8, y: top.y+1, z: z + 8 };
  const biome = getBiomeId(dim, loc);
  if (!biome || (cfg.deepDarkBlocksNatural && biome.includes("deep_dark"))) return;
  if (!allowedBiome.some(b => biome.includes(b))) return;
  const target = getBlockSafe(dim, loc);
  if (!target) return;
  cells.add(k); if (cells.size > 2000) cells.delete(cells.values().next().value); save();
  if (Math.random() > Math.min(1,cfg.naturalSpawnChance * biomeMultiplier(biome)) || inZone(dim.id, loc)) return;
  if (!SURFACES.has(top.typeId) || !isFree(target) || !hasSupport(top)) return;
  if (addPending(dim, loc, 0)) diag("natural_spore_spawn");
}, 100);
