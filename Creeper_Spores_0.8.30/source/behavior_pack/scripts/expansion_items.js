// Creeper Spores 0.4.0 — additional Survival equipment, incubation and cultivation.
// Uses supported item/block custom components; each interaction is independently revalidated.
import { world, system, BlockPermutation, ItemStack } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { NS, STATE_AGE, STATE_STRAIN, getBlockSafe, isSpore, isFree, hasSupport, belowOf, giveItem, sendActionBar, lockOnce } from "./util.js";
import { getConfig } from "./config.js";
import { historicalPods } from "./atlas.js";
import { nearbyNetworks } from "./colony_networks.js";
import { record } from "./journal.js";
import { addPending, plantSpore, knownPods } from "./spores.js";
import { STRAINS } from "./generated_data.js";
import { diag } from "./diag.js";
import { inZone } from "./zones.js";

const grenadeFlights=new Map();
function landGrenade(event){
  const id=event.projectile?.id, flight=id&&grenadeFlights.get(id);
  if(!flight)return;
  grenadeFlights.delete(id); // commit ONCE even if block + entity collision both report
  const dim=event.dimension, center=event.location;
  if(!dim||dim.id!==flight.dim)return;
  let planted=0;
  for(const [dx,dz] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]){
    const at={x:Math.floor(center.x)+dx,y:Math.floor(center.y),z:Math.floor(center.z)+dz};
    for(const dy of [0,1,-1]){
      const pos={x:at.x,y:at.y+dy,z:at.z};
      const b=getBlockSafe(dim,pos);
      if(!b||!isFree(b)||!hasSupport(belowOf(b))||inZone(dim.id,pos))continue;
      if(addPending(dim,pos,0,30)){planted++;break;}
    }
  }
  try{dim.spawnParticle("cookiedookie:spore_burst",center);}catch{}
  try{dim.playSound("cookiedookie.pod_pop",center);}catch{}
  diag("grenade_landed",{planted});
}
try{world.afterEvents.projectileHitBlock?.subscribe(landGrenade);}catch{diag("grenade_impact_block_event_unavailable");}
try{world.afterEvents.projectileHitEntity?.subscribe(landGrenade);}catch{diag("grenade_impact_entity_event_unavailable");}
system.runInterval(()=>{
  const now=system.currentTick;
  for(const [id,f] of grenadeFlights)if(now-f.started>240)grenadeFlights.delete(id);
  if(grenadeFlights.size>160)grenadeFlights.clear();
},40);

function eq(player) { try{return player.getComponent("minecraft:equippable") ?? player.getComponent("equippable");}catch{return null;} }
function hand(player) { try{return eq(player)?.getEquipment("Mainhand");}catch{return undefined;} }
function creative(player){try{return String(player.getGameMode()).toLowerCase()==="creative";}catch{return false;}}
function take(player,id,n=1) {
  if(creative(player))return true;
  try{
    const equipment=eq(player),item=equipment?.getEquipment("Mainhand");
    if(!item || item.typeId!==id || item.amount<n)return false;
    if(item.amount===n)equipment.setEquipment("Mainhand",undefined);
    else {item.amount-=n;equipment.setEquipment("Mainhand",item);}
    return true;
  }catch{return false;}
}
function worn(player,id){try{const e=eq(player);return ["Head","Chest","Legs","Feet"].some(s=>e?.getEquipment(s)?.typeId===id);}catch{return false;}}
function faceTarget(block,face){const d={Up:[0,1,0],Down:[0,-1,0],North:[0,0,-1],South:[0,0,1],East:[1,0,0],West:[-1,0,0]}[face];return d?getBlockSafe(block.dimension,{x:block.x+d[0],y:block.y+d[1],z:block.z+d[2]}):undefined;}
function nearPlayer(player,distance=8){return knownPods(player.dimension.id,player.location,distance,12).filter(p=>isSpore(getBlockSafe(player.dimension,p)));}
function damageTool(player,id,damage=1){
  if(creative(player))return;
  try{const e=eq(player),it=e.getEquipment("Mainhand");if(it?.typeId!==id)return;const d=it.getComponent("minecraft:durability");if(!d)return;if(d.damage+damage>=d.maxDurability)e.setEquipment("Mainhand",undefined);else{d.damage+=damage;e.setEquipment("Mainhand",it);}}catch{}
}
export function registerExpansionItems(reg){
  reg.registerCustomComponent(`${NS}:spore_staff`,{
    onUseOn(ev){
      try {const p=ev.source,b=ev.block;if(!p||!isSpore(b)||!lockOnce(`staff:${p.id}`,system.currentTick))return;
        const a=b.permutation.getState(STATE_AGE),cfg=getConfig();
        if(a>=7)return sendActionBar(p,"§7This pod is already mature.");
        b.setPermutation(b.permutation.withState(STATE_AGE,a+1));damageTool(p,ev.itemStack.typeId);
        sendActionBar(p,"§aThe staff advances one growth stage.");
      }catch(e){diag("staff_use_error",{msg:String(e).slice(0,80)});}
    }
  });
  // Physically thrown grenade carried by a vanilla snowball entity.
  // Projectile impact is authoritative, not the ray cursor or particle path.
  reg.registerCustomComponent(`${NS}:spore_grenade`,{
    onUse(ev){try{
      const p=ev.source;if(!p||!lockOnce(`grenade:${p.id}`,system.currentTick))return;
      const item=hand(p);if(item?.typeId!==`${NS}:spore_grenade`)return;
      const vec=p.getViewDirection(),head=p.getHeadLocation();
      const pos={x:head.x+vec.x*0.6,y:head.y+vec.y*0.6,z:head.z+vec.z*0.6};
      const snowball=p.dimension.spawnEntity("minecraft:snowball",pos);
      if(!snowball)return;
      try{snowball.applyImpulse({x:vec.x*1.35,y:vec.y*1.35+0.15,z:vec.z*1.35});}
      catch(e){try{snowball.remove();}catch{};diag("grenade_launch_motion_failed");return;}
      grenadeFlights.set(snowball.id,{dim:p.dimension.id,started:system.currentTick,owner:p.id});
      if(!take(p,`${NS}:spore_grenade`)){
        grenadeFlights.delete(snowball.id);
        try{snowball.remove();}catch{}
        return;
      }
      try{p.playSound("random.bow",{volume:0.4,pitch:1.3});}catch{}
    }catch(e){diag("grenade_launch_failed",{msg:String(e).slice(0,100)});}}
  });
  // Jar stores its contents ON the item stack; no location-dependent global inventory record.
  reg.registerCustomComponent(`${NS}:spore_jar`,{
    onUseOn(ev){try{
      const p=ev.source, equipment=eq(p),item=equipment?.getEquipment("Mainhand");
      if(!item||item.typeId!==`${NS}:spore_jar`||!lockOnce(`jar:${p.id}`,system.currentTick))return;
      const saved=item.getDynamicProperty?.("cs:contents");
      const target=ev.block;
      if(typeof saved!=="number"){
        if(!isSpore(target))return sendActionBar(p,"§7Use the empty jar on a spore pod.");
        const strain=target.permutation.getState(STATE_STRAIN)??0;
        item.setDynamicProperty("cs:contents",strain);
        equipment.setEquipment("Mainhand",item);
        target.setType("minecraft:air");
        sendActionBar(p,`§bCaptured a ${STRAINS[strain]?.name??"Common"} pod.`);
      }else{
        const dest=faceTarget(target,ev.blockFace);
        if(!dest||!isFree(dest)||!hasSupport(belowOf(dest)))return sendActionBar(p,"§7Choose empty space above firm ground.");
        plantSpore(dest,saved);
        item.setDynamicProperty("cs:contents",undefined);
        equipment.setEquipment("Mainhand",item);
        sendActionBar(p,"§aStored spore replanted.");
      }
    }catch(e){diag("jar_error",{msg:String(e).slice(0,80)});}}
  });
  reg.registerCustomComponent(`${NS}:colony_map`,{
    onUse(ev){const p=ev.source; if(!p)return;system.run(()=>openColonyMap(p));}
  });
}

export async function openColonyMap(p){
  try{
    const a=nearPlayer(p,256), f=new ActionFormData().title("Spore Colony Survey");
    let body=`Dimension: ${p.dimension.id}\nKnown loaded colonies: ${a.length}\n`;
    if(!a.length)body+="No currently observed local pods. Historical locations may still be listed.";
    else for(const b of a)body+=`\nACTIVE ${Math.round(b.dist)} blocks: ${b.x}, ${b.y}, ${b.z}`;
    record(p,'atlas');
    const connected=nearbyNetworks(p.dimension.id,p.location);
    body+=`\n\nConnected loaded colonies: ${connected.length}`;
    for(const g of connected.slice(0,5))body+=`\nNETWORK ${g.size} pods at ${g.center.x}, ${g.center.y}, ${g.center.z}`;
    if(connected.some(g=>g.size>=3))record(p,'network');
    const past=historicalPods(p.dimension.id,p.location,10);
    body+=`\n\nHistorical last-seen locations: ${past.length}`;
    for(const b of past) body+=`\nLAST SEEN ${Math.round(b.dist)} blocks: ${b.x}, ${b.y}, ${b.z}`;
    f.body(body).button("Close");
    await f.show(p);
  }catch(e){diag("colony_map_error",{msg:String(e).slice(0,80)});}
}

const incubatorLast=new Map();
export function registerExpansionBlocks(reg){
  reg.registerCustomComponent(`${NS}:incubator`,{
    onTick({block}){
      const cfg=getConfig();if(!cfg.incubatorsEnabled)return;
      try{
        const active=block.permutation.getState(`${NS}:active`)===true;
        if(!active)return;
        const k=`${block.dimension.id}:${block.x}:${block.y}:${block.z}`;
        if((incubatorLast.get(k)??-1000)+cfg.incubatorInterval>system.currentTick)return;
        const dim=block.dimension;
        for(const [x,y,z] of [[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,1,0]]){
          const b=getBlockSafe(dim,{x:block.x+x,y:block.y+y,z:block.z+z});
          if(!isSpore(b))continue;
          const age=b.permutation.getState(STATE_AGE);
          if(age>=7)continue;
          b.setPermutation(b.permutation.withState(STATE_AGE,age+1));
          incubatorLast.set(k,system.currentTick);
          if(incubatorLast.size>300)incubatorLast.clear();
          break;
        }
      }catch(e){diag("incubator_tick_error",{msg:String(e).slice(0,80)});}
    }
  });
}

async function cultivate(player,dim,pos){
  try{
    const b=getBlockSafe(dim,pos);if(b?.typeId!==`${NS}:cultivation_table`)return;
    const form=new ModalFormData().title("Spore Cultivation Table")
      .dropdown("Select strain for a nearby young common pod",STRAINS.map(s=>s.name),{defaultValueIndex:1});
    const answer=await form.show(player);
    if(answer.canceled||!answer.formValues)return;
    if(player.dimension.id!==dim.id)return;
    const choice=Number(answer.formValues[0]);
    if(!Number.isInteger(choice)||choice<1||choice>=STRAINS.length)return;
    if(getBlockSafe(dim,pos)?.typeId!==`${NS}:cultivation_table`)return;
    let target;
    for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){
      const t=getBlockSafe(dim,{x:pos.x+dx,y:pos.y,z:pos.z+dz});
      if(isSpore(t)&&t.permutation.getState(STATE_AGE)<5&&t.permutation.getState(STATE_STRAIN)===0){target=t;break;}
    }
    if(!target)return sendActionBar(player,"§7Place a young common spore beside the table.");
    const inv=player.getComponent("minecraft:inventory")?.container??player.getComponent("inventory")?.container;
    let slot=-1;
    for(let i=0;inv&&i<inv.size;i++){if(inv.getItem(i)?.typeId===`${NS}:spore_extract`){slot=i;break;}}
    if(slot<0&&!creative(player))return sendActionBar(player,"§7Requires 1 Spore Extract.");
    if(slot>=0&&!creative(player)){
      const item=inv.getItem(slot);if(item.amount===1)inv.setItem(slot,undefined);else{item.amount-=1;inv.setItem(slot,item);}
    }
    target.setPermutation(target.permutation.withState(STATE_STRAIN,choice));
    sendActionBar(player,`§aCultivated ${STRAINS[choice].name}.`);
  }catch(e){diag("cultivation_error",{msg:String(e).slice(0,80)});}
}
world.beforeEvents.playerInteractWithBlock.subscribe(ev=>{
  try{
    if(ev.isFirstEvent===false)return;
    const id=ev.block.typeId;
    if(id!==`${NS}:spore_incubator` && id!==`${NS}:cultivation_table`)return;
    if(ev.itemStack)return;
    ev.cancel=true;
    const player=ev.player,dim=ev.block.dimension,pos={...ev.block.location};
    system.run(()=>{
      const b=getBlockSafe(dim,pos);if(b?.typeId!==id)return;
      if(id===`${NS}:spore_incubator`){
        if(!getConfig().incubatorsEnabled)return sendActionBar(player,"§7Incubators are disabled.");
        const was=b.permutation.getState(`${NS}:active`)===true;
        b.setPermutation(b.permutation.withState(`${NS}:active`,!was));
        sendActionBar(player,`§aIncubator ${was?"paused":"running"}.`);
      }else{cultivate(player,dim,pos);}
    });
  }catch{}
});
