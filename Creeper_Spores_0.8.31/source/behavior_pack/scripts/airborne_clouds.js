// Finite, particle-only airborne spore carriers. No invisible invulnerable entities.
// Clouds are transient (not persisted): world blocks are saved through the normal pending-spore queue.
// A closed chunk or impassable solid block terminates a cloud; it never loads chunks on demand.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBlockSafe, hasSupport, isFree, isBarrier, belowOf, blockedBetween } from "./util.js";
import { podHooks, addPending } from "./spores.js";
import { inZone } from "./zones.js";
import { particle } from "./fx.js";
import { diag } from "./diag.js";
import { driftDirection, advanceAir, horizontalTravel } from "./airborne_math.js";
export const cloudPackets = [];
const MAX_AGE = 22; // 22 steps of 0.8 blocks: short, bounded flight
const valid = p => Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z);
function canMove(dim, pos, cfg) {
  const b=getBlockSafe(dim,{x:Math.floor(pos.x),y:Math.floor(pos.y),z:Math.floor(pos.z)}); // never assume an unloaded block is free
  if(!b || !b.isAir || isBarrier(b) || inZone(dim.id,pos))return false;
  return true;
}
function trapAt(dim,pos) {
  const x=Math.floor(pos.x),y=Math.floor(pos.y),z=Math.floor(pos.z);
  for(const [dx,dy,dz] of [[0,0,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,-1,0]]) {
    const b=getBlockSafe(dim,{x:x+dx,y:y+dy,z:z+dz});
    if(b?.typeId!=="cookiedookie:spore_trap")continue;
    try {
      const n=b.permutation.getState("cookiedookie:charges")??0;
      if(n>=4)continue;
      b.setPermutation(b.permutation.withState("cookiedookie:charges",n+1));
      return true;
    } catch {diag("trap_charge_failed");}
  }
  return false;
}
function settle(dim, at, start, strain, cfg) {
  // Descend up to 3 blocks and select the first valid floor. No teleport through a wall.
  if(!valid(at) || inZone(dim.id,at))return false;
  for(let dy=0;dy>=-3;dy--) {
    const b=getBlockSafe(dim,{x:Math.floor(at.x),y:Math.floor(at.y+dy),z:Math.floor(at.z)});
    if(!b)return false;
    if(!isFree(b))break; // cannot pass through solids
    if(!hasSupport(belowOf(b)))continue;
    if(cfg.barriersEnabled && blockedBetween(dim,start,b.location))return false;
    if(addPending(dim,b.location,strain))return true;
  }
  return false;
}
export function launchAirCloud(block,strain,cfg,random=Math.random) {
  if(!cfg.advancedTransport||!cfg.windTransport||!cfg.airClouds || cloudPackets.length>=cfg.airCloudMaxActive)return false;
  if(random()>cfg.airCloudSpawnChance)return false;
  const start={x:block.x+.5,y:block.y+1.25,z:block.z+.5};
  if(!canMove(block.dimension,start,cfg))return false;
  cloudPackets.push({dim:block.dimension,at:start,start,dir:driftDirection(world.getAbsoluteTime(),random()*10),strain,steps:0});
  return true;
}
podHooks.push((block,age,strain,cfg)=>{if(age>=5)launchAirCloud(block,strain,cfg);});
export function tickClouds() {
  const cfg=getConfig();
  if(!cfg.airClouds||!cfg.advancedTransport){cloudPackets.length=0;return;}
  // The hard cap prevents a malicious world option from creating unbounded per-tick work.
  const n=Math.min(40,cloudPackets.length), remaining=[];
  for(let i=0;i<n;i++){
    const c=cloudPackets.shift();
    if(!c)break;
    try {
      if(c.steps>=MAX_AGE||!canMove(c.dim,c.at,cfg))continue;
      // Air is simulated by a slow, continuously changing local vector.
      const wind=driftDirection(world.getAbsoluteTime(),c.steps*.03);
      const combined={x:c.dir.x*.72+wind.x*.28,y:c.dir.y*.72+wind.y*.28,z:c.dir.z*.72+wind.z*.28};
      let next=advanceAir(c.at,combined);
      if(!canMove(c.dim,next,cfg)) {
        // One turn only. If both directions are blocked, the packet stops.
        const turn={x:-combined.z,y:0,z:combined.x};
        next=advanceAir(c.at,turn);
        if(!canMove(c.dim,next,cfg))continue;
      }
      if(cfg.barriersEnabled&&blockedBetween(c.dim,c.at,next))continue;
      c.steps++;c.at=next;
      particle(c.dim,"cookiedookie:spore_mote",next,{range:24});
      if(trapAt(c.dim,next)){diag("air_trap_captured");continue;}
      if(c.steps>=3 && horizontalTravel(c.start,next)>=1.5 && Math.random()<cfg.airCloudSettleChance) {
        if(settle(c.dim,next,c.start,c.strain,cfg)){diag("air_cloud_settled");continue;}
      }
      if(c.steps<MAX_AGE)remaining.push(c);
    } catch (e) {diag("air_cloud_step_failed",{error:String(e).slice(0,60)});}
  }
  cloudPackets.push(...remaining);
  if(cloudPackets.length>cfg.airCloudMaxActive)cloudPackets.length=cfg.airCloudMaxActive;
}
system.runInterval(tickClouds,10);
