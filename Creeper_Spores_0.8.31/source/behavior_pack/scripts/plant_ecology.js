// Creeper Spores 0.4.0 — additional crops and vegetation.
// All changes are applied to the existing plant permutation; plants and player-built farms
// are never replaced with solid infection blocks. Cosmetic cues do not control growth.
import { podHooks } from "./spores.js";
import { getBlockSafe } from "./util.js";
import { diag } from "./diag.js";
const PLANTS = [
  ["minecraft:sweet_berry_bush", "growth", 3],
  ["minecraft:pumpkin_stem", "growth", 7],
  ["minecraft:melon_stem", "growth", 7],
  ["minecraft:cocoa", "age", 2],
  ["minecraft:nether_wart", "age", 3],
  ["minecraft:beetroot", "growth", 3],
];
const list = new Map(PLANTS.map(([id, state, max]) => [id, { state, max }]));
const sapling = new Set(["minecraft:oak_sapling","minecraft:spruce_sapling","minecraft:birch_sapling","minecraft:jungle_sapling","minecraft:acacia_sapling","minecraft:dark_oak_sapling","minecraft:cherry_sapling","minecraft:mangrove_propagule"]);
let effects = 0;
podHooks.push((pod,age,strain,cfg)=>{
  if (!cfg.plantEcology || age < 4) return;
  const x=pod.x+Math.floor(Math.random()*7)-3,z=pod.z+Math.floor(Math.random()*7)-3;
  const dim=pod.dimension;
  for(let dy=-2;dy<=2;dy++){
    const b=getBlockSafe(dim,{x,y:pod.y+dy,z});if(!b)continue;
    const info=list.get(b.typeId);
    if (info) {
      const n=b.permutation.getState(info.state);
      if(typeof n!=="number")return;
      if(strain===2){ if(n>0 && Math.random()<0.10)b.setPermutation(b.permutation.withState(info.state,n-1)); }
      else if(strain!==3&&strain!==4){if(n<info.max&&Math.random()<0.12)b.setPermutation(b.permutation.withState(info.state,n+1));}
      return;
    }
    // Bamboo, sugar cane and saplings are cosmetic participants; their native
    // growth is untouched because vanilla handles their growth through different mechanisms.
    if(b.typeId.includes("bamboo")||b.typeId.includes("sugar_cane")||sapling.has(b.typeId)){
      if(++effects%10===0 && Math.random()<0.25){try{dim.spawnParticle("cookiedookie:spore_mote",{x:b.x+.5,y:b.y+.7,z:b.z+.5});}catch{diag("plant_particle_missing");}}
      return;
    }
  }
});
