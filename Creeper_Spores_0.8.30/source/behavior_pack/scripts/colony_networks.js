// Creeper Spores 0.8.0: loaded-chunk, bounded colony graph. No chunk loading.
import { world, system } from '@minecraft/server';
import { getConfig } from './config.js';
import { knownPods } from './spores.js';
import { getBlockSafe, isSpore, STATE_AGE } from './util.js';
import { diag } from './diag.js';

const CONNECT = 7, MAX_NODES = 72;
let cursor=0;
const observed = new Map();
export function colonyClusters(nodes, radius=CONNECT) {
  const points=nodes.slice(0,MAX_NODES).map(p=>({...p}));
  const used=new Set(), groups=[];const r2=radius*radius;
  for(let i=0;i<points.length;i++){
    if(used.has(i))continue;
    used.add(i);const queue=[i],cluster=[];
    while(queue.length){
      const p=points[queue.shift()];cluster.push(p);
      for(let k=0;k<points.length;k++){
        if(used.has(k))continue;
        const v=points[k],dx=v.x-p.x,dy=v.y-p.y,dz=v.z-p.z;
        if(dx*dx+dy*dy+dz*dz<=r2){used.add(k);queue.push(k);}
      }
    }
    const mid={x:Math.round(cluster.reduce((s,p)=>s+p.x,0)/cluster.length),
      y:Math.round(cluster.reduce((s,p)=>s+p.y,0)/cluster.length),
      z:Math.round(cluster.reduce((s,p)=>s+p.z,0)/cluster.length)};
    groups.push({anchor:cluster.slice().sort((a,b)=>a.x-b.x||a.z-b.z||a.y-b.y)[0],size:cluster.length,mid, members:cluster});
  }
  return groups.sort((a,b)=>b.size-a.size);
}
export function nearbyNetworks(dimId, location) {
  const entry=observed.get(dimId);
  if(!entry)return [];
  return entry.groups.filter(g=>Math.hypot(g.mid.x-location.x,g.mid.y-location.y,g.mid.z-location.z)<128)
    .map(g=>({size:g.size,center:g.mid,anchor:g.anchor,observed:entry.tick}));
}
// Does not age any blocks unless networkCooperation is explicitly enabled.
system.runInterval(()=>{
  const cfg=getConfig();if(!cfg.colonyNetworks)return;
  const players=world.getPlayers();if(!players.length)return;
  const p=players[cursor++%players.length],dim=p.dimension;
  const seen=knownPods(dim.id,p.location,48,MAX_NODES);
  const live=[];
  for(const q of seen){const b=getBlockSafe(dim,q);if(isSpore(b))live.push({...q});}
  const groups=colonyClusters(live);
  observed.set(dim.id,{tick:system.currentTick,groups});
  if(observed.size>3)observed.delete(observed.keys().next().value);
  if(!cfg.networkCooperation||system.currentTick%600>=200)return;
  // At most one support event per scan, never free spore creation or a hatch override.
  for(const group of groups){
    if(group.size<3)continue;
    const candidate=group.members.find(q=>{
      const b=getBlockSafe(dim,q);return isSpore(b) && (b.permutation.getState(STATE_AGE)??7)<6;
    });
    if(!candidate)continue;
    const b=getBlockSafe(dim,candidate);if(!isSpore(b))continue;
    try {const a=b.permutation.getState(STATE_AGE);b.setPermutation(b.permutation.withState(STATE_AGE,a+1));diag('colony_network_cooperated',{size:group.size});}
    catch{diag('colony_network_update_failed');}
    break;
  }
},200);
