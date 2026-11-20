// Creeper Spores 0.8.0 - three non-destructive stage-based hybrid plants.
// Only generated in empty blocks on ordinary ground near an approved mature pod.
import { world, system, BlockPermutation } from '@minecraft/server';
import { podHooks } from './spores.js';
import { getConfig } from './config.js';
import { NS, STATE_AGE, getBlockSafe, hasSupport, belowOf, giveItem } from './util.js';
import { inZone } from './zones.js';
import { diag } from './diag.js';
import { record } from './journal.js';
const STATE_POLLINATED=`${NS}:pollinated`;
const defs={
  spore_bluebell:{strain:1,item:'luminescent_berry', ground:['grass_block','moss_block','dirt']},
  spore_bracken:{strain:0,item:'fungal_fiber', ground:['grass_block','podzol','dirt']},
  spore_bogcap:{strain:2,item:'marsh_cap', ground:['mud','mycelium','moss_block']},
};
export const HYBRID_NAMES=Object.keys(defs);
const LAST=new Map();
const POLLINATION_RECHECK_TICKS=200;
const POLLINATION_CACHE_LIMIT=512;
const HYBRID_BY_ID=new Map(HYBRID_NAMES.map(name=>[`${NS}:${name}`,name]));
function shouldScanForPollinator(key,tick){
  const last=LAST.get(key);
  if(last!==undefined&&tick-last<POLLINATION_RECHECK_TICKS)return false;
  LAST.delete(key);LAST.set(key,tick);
  if(LAST.size>POLLINATION_CACHE_LIMIT)LAST.delete(LAST.keys().next().value);
  return true;
}
/** A mature hybrid is cross-pollinated by a different mature hybrid within roughly three blocks. */
export function hasMatureCrossPollinator(block,currentName){
  for(let dx=-2;dx<=2;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-2;dz<=2;dz++){
    const d2=dx*dx+dy*dy+dz*dz;if(d2===0||d2>8)continue;
    const other=getBlockSafe(block.dimension,{x:block.x+dx,y:block.y+dy,z:block.z+dz});
    if(!other)continue;
    const otherName=HYBRID_BY_ID.get(other.typeId);
    if(!otherName||otherName===currentName)continue;
    const otherAge=other.permutation.getState(STATE_AGE);
    if(typeof otherAge==='number'&&otherAge>=3)return true;
  }
  return false;
}
function plantOne(pod,strain){
  const entries=Object.entries(defs).filter(([k,v])=>v.strain===strain);
  if(!entries.length)return;
  const [name,def]=entries[Math.floor(Math.random()*entries.length)];
  const dim=pod.dimension;
  for(let n=0;n<5;n++){
    const p={x:pod.x+Math.floor(Math.random()*7)-3,y:pod.y,z:pod.z+Math.floor(Math.random()*7)-3};
    const b=getBlockSafe(dim,p);if(!b||!b.isAir||inZone(dim.id,p))continue;
    const under=getBlockSafe(dim,{x:p.x,y:p.y-1,z:p.z});
    if(!under||!hasSupport(under)||!def.ground.some(x=>under.typeId.endsWith(x)))continue;
    try{b.setPermutation(BlockPermutation.resolve(`${NS}:${name}`,{[`${NS}:age`]:0}));return;}catch{diag('hybrid_plant_error');}
  }
}
podHooks.push((pod,age,strain,cfg)=>{
  if(!cfg.hybridPlants||age<5||Math.random()>0.018)return;
  plantOne(pod,strain);
});
export function registerHybridPlants(reg){
  for(const [key,def] of Object.entries(defs)){
    reg.registerCustomComponent(`${NS}:${key}`,{
      onTick({block}){
        try{
          if(!getConfig().hybridPlants)return;
          const age=block.permutation.getState(`${NS}:age`);
          const scanKey=`${block.dimension.id}:${block.x}:${block.y}:${block.z}`;
          if(age>=3&&block.permutation.getState(STATE_POLLINATED)!==true&&shouldScanForPollinator(scanKey,system.currentTick)&&hasMatureCrossPollinator(block,key)){
            block.setPermutation(block.permutation.withState(STATE_POLLINATED,true));
            LAST.delete(scanKey);
            try{block.dimension.spawnParticle('cookiedookie:spore_mote',{x:block.x+.5,y:block.y+.6,z:block.z+.5});}catch{}
            diag('hybrid_cross_pollinated',{plant:key});
          }
          if(typeof age==='number'&&age<3&&Math.random()<0.55)
            block.setPermutation(block.permutation.withState(`${NS}:age`,age+1));
        }catch{diag('hybrid_growth_error');}
      },
      onPlayerInteract({block,player}){
        try{
          const age=block.permutation.getState(`${NS}:age`);
          if(age<3){try{player.onScreenDisplay.setActionBar('§7This hybrid plant is still growing.');}catch{};return;}
          // Harvest commits age and pollination state before granting items, preventing repeated free harvests.
          const crossPollinated=block.permutation.getState(STATE_POLLINATED)===true;
          block.setPermutation(block.permutation.withState(`${NS}:age`,0).withState(STATE_POLLINATED,false));
          giveItem(player,`${NS}:${def.item}`,1+Math.floor(Math.random()*2)+(crossPollinated?1:0));
          if(crossPollinated)try{player.onScreenDisplay.setActionBar('§dCross-pollinated harvest: +1 bonus item.');}catch{}
          record(player,"hybrid");
          try{block.dimension.spawnParticle('cookiedookie:spore_mote',{x:block.x+.5,y:block.y+.6,z:block.z+.5});}catch{}
        }catch{diag('hybrid_harvest_error');}
      }
    });
  }
}
