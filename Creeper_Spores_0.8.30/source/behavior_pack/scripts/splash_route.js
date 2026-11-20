// 0.5.0 — opt-in spore transfer from carried strain on a splash potion impact.
// Uses the authoritative projectile event, no invented collision behavior.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBlockSafe, isFree, hasSupport, belowOf, blockedBetween } from "./util.js";
import { addPending } from "./spores.js";
import { inZone } from "./zones.js";
import { diag } from "./diag.js";
const recent = new Map();
function splash(event) {
  const cfg=getConfig();
  if(!cfg.advancedTransport||!cfg.splashPotionTransport)return;
  const source=event.source;
  if(!source || source.typeId!=="minecraft:player")return;
  let strain; try{ strain=source.getDynamicProperty("cs:carried_strain"); }catch{return;}
  if(!Number.isInteger(strain)||strain<0||strain>7)return;
  const id=event.projectile?.id;
  const type=event.projectile?.typeId??"";
  if(!id||(!type.includes("splash_potion")&&!type.includes("thrown_potion")))return;
  const now=system.currentTick;
  if((recent.get(id)??-1000)+100>now)return;
  recent.set(id,now);
  const dim=event.dimension, center=event.location;
  // Independent chances and support checks for every destination.
  let placements=0;
  for(const [dx,dz] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]){
    if(placements>=3)break;
    const target={x:Math.floor(center.x)+dx,y:Math.floor(center.y),z:Math.floor(center.z)+dz};
    const b=getBlockSafe(dim,target);
    if(!b||!isFree(b)||!hasSupport(belowOf(b))||inZone(dim.id,target))continue;
    if(cfg.barriersEnabled&&blockedBetween(dim,source.location,target))continue;
    if(Math.random()<cfg.transportChance&&addPending(dim,target,strain,90))placements++;
  }
  if(placements)diag("splash_spores_transmitted",{placements});
  if(recent.size>300)recent.clear();
}
try{world.afterEvents.projectileHitBlock?.subscribe(splash);}catch{diag("potion_block_event_unavailable");}
try{world.afterEvents.projectileHitEntity?.subscribe(splash);}catch{diag("potion_entity_event_unavailable");}
