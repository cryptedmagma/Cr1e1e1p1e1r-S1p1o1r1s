// Creeper Spores 0.8.0: best-effort player-placement provenance.
// Remembers eligible placed blocks from THIS version forward only. Unknown older blocks
// remain unknown, never claimed to be naturally generated.
import { world,system } from '@minecraft/server';
import {diag} from './diag.js';
const KEY='cs:placed_block_memory_080',MAX=600;
let memory=null,dirty=false;
const key=(d,p)=>`${d}:${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`;
function load(){
  if(memory)return;
  memory=new Map();
  try{const raw=world.getDynamicProperty(KEY);const a=JSON.parse(typeof raw==='string'?raw:'[]');
    if(Array.isArray(a))for(const x of a.slice(-MAX))if(typeof x==='string'&&x.length<110)memory.set(x,true);
  }catch{diag('placed_guard_corrupt');}
}
export function knownPlayerPlaced(dimId,p){load();return memory.has(key(dimId,p));}
export function rememberPlaced(dimId,p){load();const k=key(dimId,p);memory.delete(k);memory.set(k,true);if(memory.size>MAX)memory.delete(memory.keys().next().value);dirty=true;}
export function forgetPlaced(dimId,p){load();dirty=memory.delete(key(dimId,p))||dirty;}
try{world.afterEvents.playerPlaceBlock?.subscribe(ev=>{
  try{if(ev.block?.typeId?.startsWith('minecraft:'))rememberPlaced(ev.block.dimension.id,ev.block.location);}catch{}
});}catch{diag('placed_guard_event_missing');}
try{world.afterEvents.playerBreakBlock?.subscribe(ev=>{
  try{forgetPlaced(ev.block.dimension.id,ev.block.location);}catch{}
});}catch{}
system.runInterval(()=>{if(!dirty)return;load();try{world.setDynamicProperty(KEY,JSON.stringify([...memory.keys()]));dirty=false;}catch{diag('placed_guard_save_failed');}},200);
