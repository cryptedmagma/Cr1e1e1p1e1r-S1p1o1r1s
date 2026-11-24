// Optional designed micro-ruins: never edits existing solid blocks, crops or containers.
// One observed cell is attempted once; only in loaded Overworld terrain near players.
import {world,system} from '@minecraft/server';
import {getConfig} from './config.js';
import {getBlockSafe,getBiomeId,hasSupport} from './util.js';
import {inZone} from './zones.js';
import {diag} from './diag.js';
import {knownPlayerPlaced} from './placed_block_guard.js';
import {safeStructureCell,cellIsProtected} from './structure_guard.js';
const KEY='cs:field_ruin_cells_080';
let cells=null,turn=0;
function load(){if(cells)return;try{const a=JSON.parse(world.getDynamicProperty(KEY)??'[]');cells=new Set(Array.isArray(a)?a.slice(-350):[]);}catch{cells=new Set();}}
function save(){try{world.setDynamicProperty(KEY,JSON.stringify([...cells].slice(-350)));}catch{diag('ruin_save_failed');}}
export const RUIN_DESIGNS=[
  {id:'lantern_ring',blocks:[
    [0,0,0,'cookiedookie:spore_nest'],[2,0,0,'cookiedookie:spore_lantern'],[-2,0,0,'cookiedookie:spore_lantern'],
    [0,0,2,'minecraft:moss_carpet'],[0,0,-2,'minecraft:moss_carpet'],
  ]},
  {id:'moss_stones',blocks:[
    [0,0,0,'cookiedookie:spore_nest'],[1,0,0,'cookiedookie:infected_moss_block'],[-1,0,0,'cookiedookie:infected_moss_block'],
    [0,0,1,'cookiedookie:spore_torch'],[0,0,-1,'cookiedookie:spore_torch'],
  ]},
  {id:'field_markers',blocks:[
    [0,0,0,'cookiedookie:spore_nest'],[2,0,0,'cookiedookie:spore_lantern'],[-2,0,0,'cookiedookie:spore_lantern'],
    [0,0,2,'cookiedookie:infected_moss_block'],[0,0,-2,'cookiedookie:infected_moss_block'],
    [1,0,1,'cookiedookie:spore_torch'],[-1,0,-1,'cookiedookie:spore_torch'],
  ]},
];
export const RUIN_DESIGN=RUIN_DESIGNS[0].blocks;
export function validRuinSite(dim,center,design=RUIN_DESIGN){
  if(inZone(dim.id,center))return false;
  for(const [dx,dy,dz] of design){
    const p={x:center.x+dx,y:center.y+dy,z:center.z+dz},b=getBlockSafe(dim,p);
    const floor=getBlockSafe(dim,{x:p.x,y:p.y-1,z:p.z});
    // Every cell (not only the centre) must be empty, unprotected and outside quarantine.
    if(!safeStructureCell(dim,b)||!floor||cellIsProtected(floor.typeId)||!hasSupport(floor))return false;
    if(knownPlayerPlaced(dim.id,{x:p.x,y:p.y-1,z:p.z}))return false;
    // Do not replace a player-built platform or a suspicious surface.
    if(!['minecraft:grass_block','minecraft:dirt','minecraft:moss_block','minecraft:podzol','minecraft:mud'].includes(floor.typeId))return false;
  }
  return true;
}
system.runInterval(()=>{
  const cfg=getConfig();if(!cfg.fieldRuins)return;
  const ps=world.getPlayers();if(!ps.length)return;
  load();const p=ps[turn++%ps.length],dim=p.dimension;
  if(!dim.id.includes('overworld'))return;
  const cx=Math.floor(p.location.x/64),cz=Math.floor(p.location.z/64),key=`${dim.id}:${cx}:${cz}`;
  if(cells.has(key))return;
  // At most one attempt per cell; no brute-force scanning or underground loading.
  const biome=getBiomeId(dim,p.location);
  if(!biome||biome.includes('deep_dark')||!/(plains|meadow|forest|taiga|lush)/.test(biome))return;
  const center={x:Math.floor(p.location.x)+8,y:Math.floor(p.location.y),z:Math.floor(p.location.z)+8};
  if(!validRuinSite(dim,center))return;
  cells.add(key);if(cells.size>350)cells.delete(cells.values().next().value);save();
  // Mark the cell BEFORE placement; a partial attempt won't duplicate after reload.
  if(Math.random()>0.16)return;
  for(const [dx,dy,dz,id] of design.blocks){
    const b=getBlockSafe(dim,{x:center.x+dx,y:center.y+dy,z:center.z+dz});
    if(!safeStructureCell(dim,b))break; // re-checked at write time
    try{b.setType(id);}catch{diag('ruin_placement_failed');break;}
  }
  diag('field_ruin_observed',{design:design.id});
},600);
