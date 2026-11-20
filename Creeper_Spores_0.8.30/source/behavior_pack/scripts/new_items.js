// New 0.7 survival item behavior, no extra entity types and no intrusive vanilla overrides.
import {system} from "@minecraft/server";
import {getBlockSafe,isFree,hasSupport,belowOf,isCreative,lockOnce,sendActionBar} from "./util.js";
import {addPending} from "./spores.js";
import {diag} from "./diag.js";
const dirs={Up:[0,1,0],Down:[0,-1,0],North:[0,0,-1],South:[0,0,1],East:[1,0,0],West:[-1,0,0]};
export function registerNewItems(reg){
  reg.registerCustomComponent("cookiedookie:spore_capsule",{
    onUseOn(ev){
      try{
        const p=ev.source,b=ev.block, offset=dirs[ev.blockFace];
        if(!p||!b||!offset||!lockOnce(`capsule:${p.id}`,system.currentTick))return;
        const loc={x:b.x+offset[0],y:b.y+offset[1],z:b.z+offset[2]};
        const fresh=getBlockSafe(b.dimension,loc);
        if(!isFree(fresh)||!hasSupport(belowOf(fresh)))return sendActionBar(p,"§7Capsule requires free space above stable ground.");
        // Preserve world state if pending cap, duplicate location, or quarantine rejects deposit.
        if(!addPending(b.dimension,fresh.location,0,40))return sendActionBar(p,"§7Capsule could not release a spore here.");
        if(!isCreative(p)){
          const eq=p.getComponent("minecraft:equippable")??p.getComponent("equippable");
          const item=eq?.getEquipment("Mainhand");
          if(item?.typeId==="cookiedookie:spore_capsule"){
            if(item.amount<=1)eq.setEquipment("Mainhand",undefined);
            else{item.amount-=1;eq.setEquipment("Mainhand",item);}
          }
        }
        sendActionBar(p,"§aMicroscopic spore released. It will germinate shortly.");
      }catch(e){diag("capsule_use_failed",{error:String(e).slice(0,80)});}
    }
  });
}
