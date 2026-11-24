// Best-effort Bedrock liquid-level checks. This is not an exact fluid simulation.
import { getBlockSafe, isFree, hasSupport, belowOf } from "./util.js";
export function liquidDepth(block) {
  try { const d=block?.permutation?.getState("liquid_depth");return typeof d==="number"?d:null; }catch{return null;}
}
export function waterRoute(dim,start,random=Math.random) {
  const dirs=[[1,0],[-1,0],[0,1],[0,-1]];
  const candidates=[];
  for(const [dx,dz] of dirs) {
    const first=getBlockSafe(dim,{x:start.x+dx,y:start.y,z:start.z+dz});
    if(first?.typeId!=="minecraft:water")continue;
    const dest=getBlockSafe(dim,{x:start.x+dx*2,y:start.y,z:start.z+dz*2});
    // No skipping across unloaded chunks, no water teleport through a wall.
    if(!dest)continue;
    const floor=getBlockSafe(dim,{x:start.x+dx*2,y:start.y-1,z:start.z+dz*2});
    const firstDepth=liquidDepth(first),secondDepth=liquidDepth(dest);
    const lower=getBlockSafe(dim,{x:first.x,y:first.y-1,z:first.z});
    let weight=1;
    if(firstDepth!==null&&secondDepth!==null&&secondDepth>=firstDepth)weight+=3;
    if(lower?.typeId==="minecraft:water")weight+=1;
    if(isFree(dest)&&hasSupport(floor))candidates.push({pos:dest.location,weight});
    // Edge of water: airborne/spore land deposition alongside stream remains possible.
    if(dest.isAir&&hasSupport(floor))candidates.push({pos:dest.location,weight:weight+1});
  }
  if(!candidates.length)return null;
  const sum=candidates.reduce((n,c)=>n+c.weight,0),cut=random()*sum;
  let used=0;
  for(const c of candidates){used+=c.weight;if(used>=cut)return c.pos;}
  return candidates[candidates.length-1].pos;
}
