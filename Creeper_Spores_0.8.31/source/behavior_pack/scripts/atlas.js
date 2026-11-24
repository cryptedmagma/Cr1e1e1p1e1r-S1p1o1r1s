// Persistent, bounded last-seen colony atlas. Textual history (NOT a native drawn map).
// Captures location only after a loaded pod has actually been observed; no chunk scanning.
import {world,system} from "@minecraft/server";
const KEY="cs:colony_atlas_v1", LIMIT=160;
let records=null,dirty=false;
function load(){
  if(records)return;
  records=new Map();
  try{
    const raw=world.getDynamicProperty(KEY),arr=JSON.parse(typeof raw==="string"?raw:"[]");
    if(Array.isArray(arr))for(const p of arr.slice(-LIMIT)){
      if(p&&typeof p.dim==="string"&&[p.x,p.y,p.z,p.seen].every(Number.isFinite))
        records.set(`${p.dim}:${p.x}:${p.y}:${p.z}`,p);
    }
  }catch{}
}
export function rememberPod(dim,loc,strain=0){
  load();
  const x=Math.floor(loc.x),y=Math.floor(loc.y),z=Math.floor(loc.z);
  const key=`${dim}:${x}:${y}:${z}`;
  if(records.has(key))return false;
  let now=0;try{now=world.getAbsoluteTime();}catch{}
  records.set(key,{dim,x,y,z,strain,seen:now});
  if(records.size>LIMIT)records.delete(records.keys().next().value);
  dirty=true;
  return true;
}
export function historicalPods(dim,near,max=12){
  load();
  return [...records.values()].filter(p=>p.dim===dim)
  .map(p=>({...p,dist:Math.hypot(p.x-near.x,p.y-near.y,p.z-near.z)}))
  .sort((a,b)=>a.dist-b.dist).slice(0,max);
}
export function flushAtlas(){
  if(!dirty)return;
  try{world.setDynamicProperty(KEY,JSON.stringify([...records.values()]));dirty=false;}catch{}
}
system.runInterval(flushAtlas,200);
