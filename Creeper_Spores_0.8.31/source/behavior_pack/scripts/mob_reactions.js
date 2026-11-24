// Creeper Spores 0.4.0 — local, bounded mob responses. No overriding vanilla AI or player choices.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBlockSafe, isSpore, STATE_AGE, STATE_STRAIN } from "./util.js";
import { diag } from "./diag.js";
const last = new Map();
const effects = {
  "minecraft:cow":"slowness", "minecraft:sheep":"slowness", "minecraft:pig":"slowness",
  "minecraft:chicken":"slowness", "minecraft:rabbit":"slowness", "minecraft:wolf":"slowness",
  "minecraft:cat":"slowness", "minecraft:fox":"slowness", "minecraft:bee":"slowness",
  "minecraft:frog":"slowness", "minecraft:allay":"slowness",
  "minecraft:zombie":"weakness", "minecraft:skeleton":"weakness", "minecraft:spider":"slowness",
  "minecraft:enderman":"weakness", "minecraft:witch":"weakness", "minecraft:slime":"weakness",
  "minecraft:warden":"weakness"
};
let index=0;
system.runInterval(()=>{
  const cfg=getConfig(); if(!cfg.mobReactions)return;
  const players=world.getPlayers(); if(!players.length)return;
  const p=players[index++%players.length], dim=p.dimension;
  let entities=[];try{entities=dim.getEntities({location:p.location,maxDistance:16});}catch{return;}
  let checked=0;
  for(const mob of entities){
    if(++checked>24)break;
    const type=mob.typeId, fx=effects[type];
    if(!fx && type!=="minecraft:villager" && type!=="minecraft:villager_v2" && type!=="minecraft:iron_golem")continue;
    try {
      const pos={x:Math.floor(mob.location.x),y:Math.floor(mob.location.y),z:Math.floor(mob.location.z)};
      let pod;
      // Include nearby flyers and swimmers; their body origin can sit above/below the pod.
      for(const dy of [-1,0,1,2]){
        for(const [dx,dz] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]){
          const b=getBlockSafe(dim,{x:pos.x+dx,y:pos.y+dy,z:pos.z+dz});
          if(isSpore(b)&&b.permutation.getState(STATE_AGE)>=4){pod=b;break;}
        }
        if(pod)break;
      }
      if(!pod)continue;
      if((last.get(mob.id)??-99999)+200>system.currentTick)continue;
      last.set(mob.id,system.currentTick);
      const strain=pod.permutation.getState(STATE_STRAIN)??0;
      if(fx && strain===2) mob.addEffect(fx,60,{amplifier:0});
      else if(!fx && cfg.villagerReactions){dim.playSound("mob.villager.hmm",mob.location,{volume:0.2});}
      if(type==="minecraft:iron_golem" && strain===2){try{mob.addTag("cs_defending_colony");}catch{}}
    } catch {diag("mob_reaction_failed");}
  }
  if(last.size>1500)last.clear();
},100);
