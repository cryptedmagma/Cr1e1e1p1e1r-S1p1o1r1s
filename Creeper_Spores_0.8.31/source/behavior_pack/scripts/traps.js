// Empty-hand use harvests stored captured air clouds; block-state charge survives reloads.
import {world,system} from "@minecraft/server";
import { getBlockSafe, giveItem, sendActionBar, lockOnce } from "./util.js";
import { diag } from "./diag.js";
world.beforeEvents.playerInteractWithBlock.subscribe(ev=>{
  if(ev.block?.typeId!=="cookiedookie:spore_trap"||ev.isFirstEvent===false||ev.itemStack)return;
  ev.cancel=true;
  const player=ev.player,dim=ev.block.dimension,pos={...ev.block.location};
  system.run(()=>{
    try {
      const b=getBlockSafe(dim,pos); if(b?.typeId!=="cookiedookie:spore_trap")return;
      if(!lockOnce(`trap:${dim.id}:${pos.x}:${pos.y}:${pos.z}`,system.currentTick))return;
      const n=b.permutation.getState("cookiedookie:charges")??0;
      if(n<=0)return sendActionBar(player,"§7Trap is empty. Place it near drifting spores.");
      b.setPermutation(b.permutation.withState("cookiedookie:charges",0));
      giveItem(player,"cookiedookie:spore_extract",n);
      sendActionBar(player,`§aRecovered ${n} Spore Extract from the trap.`);
    }catch(e){diag("spore_trap_harvest_error",{error:String(e).slice(0,70)});}
  });
});
