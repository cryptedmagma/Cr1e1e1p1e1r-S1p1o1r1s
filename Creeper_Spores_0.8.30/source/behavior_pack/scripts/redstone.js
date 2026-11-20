import { world, system, ItemStack } from "@minecraft/server";
import {
  NS, STATE_AGE, getBlockSafe, isSpore, isFree, hasSupport, belowOf, blockedBetween, sendActionBar,
} from "./util.js";
import { getConfig } from "./config.js";
import { addZone, inZone } from "./zones.js";
import { podYield, addPending, clearPendingNear } from "./spores.js";
import { diag } from "./diag.js";
import { cue } from "./fx.js";

// Spore Controller block. Reads redstone power at its own position (polled every 5 ticks), acts on a RISING edge only
// (continuous power never repeats the action), honours a per-controller cooldown and bounded scan radius.
// Modes: accelerate, suppress, harvest, auto-harvest, and powered auto-seeding.
// Auto-seed consumes one adjacent spore extract per queued spore and respects barriers/zones.
const MODE_NAMES = ["Accelerate", "Suppress", "Harvest", "Auto Harvest", "Auto Seed"];
const R = 3, CAP = 8;
const last = new Map();                               // pos key -> tick of last action

function scan(block, pred) {
  const out = [];
  for (let x = -R; x <= R && out.length < CAP; x++) for (let z = -R; z <= R && out.length < CAP; z++) for (let y = -1; y <= 2 && out.length < CAP; y++) {
    const b = getBlockSafe(block.dimension, { x: block.x + x, y: block.y + y, z: block.z + z });
    if (isSpore(b) && pred(b.permutation.getState(STATE_AGE))) out.push(b);
  }
  return out;
}

function routeDrops(block,items){
  const dim=block.dimension;
  const container=adjacentContainer(block);
  const drop={x:block.x+.5,y:block.y+1.3,z:block.z+.5};
  for(const [id,n] of items){
    if(n<=0)continue;
    try{let left=new ItemStack(id,n);
      if(container)left=container.addItem(left);
      if(left)dim.spawnItem(left,drop);
    }catch{diag("controller_drop_failed");}
  }
}
function adjacentContainer(block){
  for(const [dx,dy,dz] of [[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,-1,0]]){
    try{const b=getBlockSafe(block.dimension,{x:block.x+dx,y:block.y+dy,z:block.z+dz});
      const c=b?.getComponent("minecraft:inventory")?.container;
      if(c)return c;
    }catch{}
  }
  return undefined;
}
function extractorSlot(container){
  if(!container)return -1;
  try{for(let i=0;i<container.size;i++){const item=container.getItem(i);if(item?.typeId===`${NS}:spore_extract`&&item.amount>0)return i;}}catch{}
  return -1;
}
function autoSeed(block){
  const dim=block.dimension,container=adjacentContainer(block),slot=extractorSlot(container);
  if(slot<0){diag("controller_seed_no_extract");return false;}
  const sources=scan(block,a=>a>=3);
  if(!sources.length){diag("controller_seed_no_mature_pod");return false;}
  let source=null,target=null;
  for(const pod of sources){
    const strain=pod.permutation.getState(`${NS}:strain`)??0;
    for(let radius=1;radius<=R&&!target;radius++){
      for(let x=-radius;x<=radius&&!target;x++)for(let z=-radius;z<=radius&&!target;z++){
        if(Math.max(Math.abs(x),Math.abs(z))!==radius)continue;
        const b=getBlockSafe(dim,{x:pod.x+x,y:pod.y,z:pod.z+z});
        if(!b||!isFree(b)||!hasSupport(belowOf(b)))continue;
        if(inZone(dim.id,b.location))continue;
        if(getConfig().barriersEnabled&&blockedBetween(dim,pod.location,b.location))continue;
        source={pod,strain};target=b;break;
      }
    }
    if(target)break;
  }
  if(!target){diag("controller_seed_no_valid_site");return false;}
  if(!addPending(dim,target.location,source.strain)){diag("controller_seed_queue_rejected");return false;}
  try{
    const item=container.getItem(slot);
    if(!item||item.typeId!==`${NS}:spore_extract`||item.amount<1){clearPendingNear(dim.id,target.location,0);diag("controller_seed_input_changed");return false;}
    container.setItem(slot,item.amount===1?undefined:new ItemStack(item.typeId,item.amount-1));
  }catch{clearPendingNear(dim.id,target.location,0);diag("controller_seed_consume_failed");return false;}
  diag("controller_seed_queued",{strain:source.strain,x:target.x,y:target.y,z:target.z});
  return true;
}
function act(block, mode) {
  const dim = block.dimension;
  if (mode === 0) {
    for (const b of scan(block, a => a < 7)) {                         // one stage per edge, per pod, never past maturity
      const age = b.permutation.getState(STATE_AGE);
      b.setPermutation(b.permutation.withState(STATE_AGE, age + 1));
    }
  } else if (mode === 2 || mode === 3) {
    for (const b of scan(block, a => a >= 3)) {
      const age = b.permutation.getState(STATE_AGE), strain = b.permutation.getState("cookiedookie:strain") ?? 0;
      b.setPermutation(b.permutation.withState(STATE_AGE, 1));
      routeDrops(block,podYield(age,strain));
    }
  } else if(mode===4){
    autoSeed(block);
  }
}

function tick(block) {
  const cfg = getConfig();
  if (!cfg.redstoneControllers) return;
  if (typeof block.getRedstonePower !== "function") { diag("redstone_api_missing"); return; }
  let power;
  try { power = block.getRedstonePower(); } catch { return; }
  const on = (power ?? 0) > 0;
  const perm = block.permutation;
  const was = perm.getState(`${NS}:powered`) === true;
  const mode = perm.getState(`${NS}:mode`) ?? 0;
  if (on && mode === 1) addZone(block.dimension.id, block.location, 3, 60);
  const key = `${block.dimension.id}:${block.x}:${block.y}:${block.z}`;
  const now = system.currentTick;
  if (on && (mode === 3 || mode === 4) && (last.get(key) ?? -1e9) + cfg.controllerCooldown <= now) {
    last.set(key,now);
    act(block,mode); // bounded, powered mode; unlike edge-triggered harvest
    if(last.size>256)last.delete(last.keys().next().value);
  }
  if (on === was) return;
  block.setPermutation(perm.withState(`${NS}:powered`, on));
  if (!on) return;                                                           // falling edge: state only
  if ((last.get(key) ?? -1e9) + cfg.controllerCooldown > now) { diag("controller_cooldown"); return; }
  last.set(key, now);
  if (last.size > 256) last.delete(last.keys().next().value);
  if(mode!==3&&mode!==4)act(block, mode);
  cue(block.dimension, { x: block.x + 0.5, y: block.y + 1, z: block.z + 0.5 }, { snd: "random.click" });
}

export function registerController(reg) {
  reg.registerCustomComponent(`${NS}:controller`, { onTick({ block }) { try { tick(block); } catch (e) { diag("controller_error", { err: String(e).slice(0, 80) }); } } });
}

// Empty-hand use cycles the mode (validated again when the delayed write runs).
world.beforeEvents.playerInteractWithBlock.subscribe(ev => {
  if (ev.itemStack || ev.isFirstEvent === false || ev.block.typeId !== `${NS}:spore_controller`) return;
  const player = ev.player, dim = ev.block.dimension, pos = ev.block.location;
  system.run(() => {
    try {
      if (player.isValid === false) return;
      const b = getBlockSafe(dim, pos);
      if (!b || b.typeId !== `${NS}:spore_controller`) return;
      const mode = ((b.permutation.getState(`${NS}:mode`) ?? 0) + 1) % MODE_NAMES.length;
      b.setPermutation(b.permutation.withState(`${NS}:mode`, mode));
      sendActionBar(player, `§eController mode: ${MODE_NAMES[mode]}`);
    } catch { /* stale */ }
  });
});
