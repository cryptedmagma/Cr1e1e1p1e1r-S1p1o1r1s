// Creeper Spores 0.6.4 - purely cosmetic, low-cost, universal living-mob infection.
// NO attached spore bud, NO creeper-faced shoulder object, NO replacement mob or vanilla skin.
// Spawn at most one bounded bundle per infected mob per second, with global per-scan budget.
import { getPrefs } from "./fx.js";
export const VISUAL_BUDGET = 24;
const NS = 'cookiedookie:infection_';
const previous = new Map();
const safe = p => !!p && Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z);
export const fxName = suffix => NS + suffix;
export function eligibleViewers(dim, location, range=24) {
  try {return dim.getPlayers({location,maxDistance:range}).some(p=>getPrefs(p).particles>0);}catch{return false;}
}
// Pure offset geometry exported for offline tests. Subtle cosmetics on many body types;
// orientation is approximate and never claims to recolor an entity's real eye texture.
export function visualPoints(origin, head, dir) {
  if(!safe(origin)||!safe(head)) return null;
  const dx=Number.isFinite(dir?.x)?dir.x:0, dz=Number.isFinite(dir?.z)?dir.z:1;
  const l=Math.hypot(dx,dz)||1, f={x:dx/l,z:dz/l};
  const side={x:-f.z,z:f.x}, height=Math.max(0.4,Math.min(5,head.y-origin.y));
  const point=(front,across,y)=>({x:origin.x+front*f.x+across*side.x,y,z:origin.z+front*f.z+across*side.z});
  return {
    mouth:point(0.28,0,head.y-0.26),
    nose:point(0.31,0.10,head.y-0.18),
    eyeLeft:point(0.20,-0.17,head.y-0.08),
    eyeRight:point(0.20,0.17,head.y-0.08),
    side:point(-0.23,0.28,origin.y+height*0.58),
    leg:point(0.05,0.18,origin.y+height*0.22),
    back:point(-0.30,0,origin.y+height*0.77),
    breath:point(0.43,0,head.y-0.16),
    ground:point(-0.20,0,origin.y+0.06),
    center:point(0,0,origin.y+height*0.45)
  };
}
function emit(dim,type,pos){if(!safe(pos))return;try{dim.spawnParticle(fxName(type),pos);}catch{} }
function trace(e){
  let pos,head,dir;
  try{pos=e.location;head=e.getHeadLocation?.()??{...pos,y:pos.y+1};dir=e.getViewDirection?.()??{x:0,y:0,z:1};}catch{return null;}
  return visualPoints(pos,head,dir);
}
// cfg quality 1: 3-5 tiny cues/s; quality 2: 5-9 cues/s. Alternating cues
// preserve all 9 passive effects without all of them continuously emitting.
export function renderCarrier(e, tick, cfg) {
  if(!cfg.infectionVisuals || cfg.infectionVisualQuality<=0)return false;
  const t=trace(e); if(!t)return false;
  if(!eligibleViewers(e.dimension,e.location,cfg.infectionVisualRange??24))return false;
  const q=cfg.infectionVisualQuality;
  const phase=Math.abs(hashCode(e.id)+Math.floor(tick/20))%4;
  // Green slime from mouth + nose, faint stains, and a small eye glint.
  emit(e.dimension,'goo',t.mouth);
  if(q>=2)emit(e.dimension,'goo',t.nose);
  emit(e.dimension,'stain',t.side);
  emit(e.dimension,'eyes',phase%2?t.eyeLeft:t.eyeRight);
  // Rotate moss, glow, tiny mushroom and low-density dust/breath to avoid overdraw.
  if(phase===0){emit(e.dimension,'glow',t.leg);if(q>=2)emit(e.dimension,'moss',t.back);}
  if(phase===1){emit(e.dimension,'moss',t.back);if(q>=2)emit(e.dimension,'glow',t.side);}
  if(phase===2){emit(e.dimension,'mushroom',t.back);if(q>=2)emit(e.dimension,'breath',t.breath);}
  if(phase===3){emit(e.dimension,'breath',t.breath);if(q>=2)emit(e.dimension,'dust',t.center);}
  // Movement-only slime footprints, short lifetime and no world block changes.
  let moved=false;
  const prev=previous.get(e.id),loc=e.location;
  if(prev && prev.dimension===e.dimension.id) {
    const distance=Math.hypot(loc.x-prev.x,loc.y-prev.y,loc.z-prev.z);
    moved=Number.isFinite(distance)&&distance>0.16&&distance<10;
  }
  previous.set(e.id,{x:loc.x,y:loc.y,z:loc.z,dimension:e.dimension.id});
  if(moved && (q>=2||phase===0))emit(e.dimension,'footprint',t.ground);
  if(previous.size>2048)previous.clear();
  return true;
}
function hashCode(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return h;}
// Short one-shot events; cosmetic failures must not affect drops or cleanup.
export function sporeShedding(dim,location,cfg) {
  if(!cfg.infectionVisuals||cfg.infectionVisualQuality<=0)return;
  if(!eligibleViewers(dim,location,cfg.infectionVisualRange??24))return;
  emit(dim,'shed',{x:location.x,y:location.y+0.3,z:location.z});
}
export function carrierCleaned(e,cfg) {
  previous.delete(e.id);
  if(!cfg.infectionVisuals||cfg.infectionVisualQuality<=0)return;
  try{const p=trace(e);if(p&&eligibleViewers(e.dimension,e.location,cfg.infectionVisualRange??24)) emit(e.dimension,'clean',p.center);}catch{}
}
export function deathShedding(dim,location,cfg){sporeShedding(dim,location,cfg);}
