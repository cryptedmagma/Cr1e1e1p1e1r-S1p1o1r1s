// Creeper Spores 0.8.0: bounded, opt-in environmental adaptations for all 23 variants.
// Never modifies normal creeper AI, targets, explosions, drops, or nearby vanilla mobs.
import { world,system } from '@minecraft/server';
import { VARIANTS } from './generated_data.js';
import { getConfig } from './config.js';
import { getBlockSafe } from './util.js';
import { diag } from './diag.js';
const byId=Object.fromEntries(Object.entries(VARIANTS).map(([k,v])=>[v.id,k]));
const rules={
  moss:['regeneration','moss',0],cave:['speed','stone',0],crystal:['resistance','deepslate',0],
  swamp:['resistance','mud',0],desert:['speed','sand',0],snow:['resistance','snow',0],
  jungle:['jump_boost','leaves',0],mushroom:['regeneration','mycelium',0],
  sculk:['resistance','sculk',0],nether:['fire_resistance','nether',0],
  end:['slow_falling','end',0],water:['water_breathing','water',0],lava:['fire_resistance','lava',0],
  flower:['regeneration','flowers',0],thorn:['resistance','leaves',0],phantom:['slow_falling','air',0],
  giant:['resistance','ground',0],miniature:['speed','ground',0],glowing:['night_vision','dark',0],
  spore_queen:['regeneration','ground',0],grass_crown:['regeneration','grass',0],
  carved_wood:['resistance','wood',0],slender_green:['speed','bamboo',0]
};
export const variantAbilityKeys=Object.keys(rules);
function environmentOk(mode, mob, floor, at){
  const f=floor?.typeId??'',a=at?.typeId??'',id=mob.dimension.id;
  switch(mode){
    case 'ground':return !!floor?.isSolid;
    case 'air':return a==='minecraft:air';
    case 'dark':return mob.location.y<48;
    case 'nether':return id.includes('nether');
    case 'end':return id.includes('the_end');
    case 'moss':return f.includes('moss');
    case 'stone':return f.includes('stone')||f.includes('deepslate');
    case 'deepslate':return f.includes('deepslate')||mob.location.y<0;
    case 'mud':return f.includes('mud');
    case 'sand':return f.includes('sand');
    case 'snow':return f.includes('snow')||f.includes('ice');
    case 'leaves':return f.includes('leaves')||a.includes('leaves');
    case 'mycelium':return f.includes('mycelium');
    case 'sculk':return f.includes('sculk');
    case 'water':return a==='minecraft:water'||f==='minecraft:water';
    case 'lava':return a==='minecraft:lava'||f==='minecraft:lava';
    case 'flowers':return a.includes('flower')||f.includes('moss')||f==='minecraft:grass_block';
    case 'grass':return f==='minecraft:grass_block';
    case 'wood':return f.includes('log')||f.includes('planks');
    case 'bamboo':return a.includes('bamboo')||f.includes('bamboo');
    default:return false;
  }
}
let playerCursor=0;
system.runInterval(()=>{
  if(!getConfig().variantEcology)return;
  const ps=world.getPlayers();if(!ps.length)return;
  const p=ps[playerCursor++%ps.length];let nearby=[];
  try{nearby=p.dimension.getEntities({location:p.location,maxDistance:28});}catch{return;}
  let n=0;
  for(const e of nearby){
    if(n>=24)break;
    const key=byId[e.typeId];if(!key)continue;n++;
    try{
      const [effect,mode,amp]=rules[key];const raw=e.location;
      const pos={x:Math.floor(raw.x),y:Math.floor(raw.y),z:Math.floor(raw.z)};
      const at=getBlockSafe(e.dimension,pos),floor=getBlockSafe(e.dimension,{x:pos.x,y:pos.y-1,z:pos.z});
      if(!environmentOk(mode,e,floor,at))continue;
      e.addEffect(effect,125,{amplifier:amp,showParticles:false});
    }catch{diag('variant_ecology_fail',{key});}
  }
},100);
