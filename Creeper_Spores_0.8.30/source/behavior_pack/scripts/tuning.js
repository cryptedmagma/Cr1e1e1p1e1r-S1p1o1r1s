// Creeper Spores 0.4.0 — independent, per-substrate and per-biome numeric tuning.
// All unspecified conditions are NEUTRAL (1.0); contradictory old answers are not guessed.
import { world } from "@minecraft/server";
const KEY="cs:local_tuning_v1";
export const SUBSTRATES=["grass_block","dirt","coarse_dirt","dirt_with_roots","mud","muddy_mangrove_roots","moss_block","podzol","mycelium","farmland","sand","red_sand","gravel","clay","stone","deepslate","netherrack","soul_soil","end_stone","sculk"];
export const BIOMES=["plains","sunflower_plains","forest","flower_forest","birch_forest","old_growth_taiga","snowy_taiga","snowy_plains","swamp","mangrove_swamp","desert","savanna","badlands","jungle","bamboo_jungle","cherry_grove","pale_garden","mushroom_fields","lush_caves"];
let state=null;
function load(){
 if(state)return state;
 try{
  const v=JSON.parse(world.getDynamicProperty(KEY)??"{}");
  state={growth:{},biome:{},revision:0};
  if(v&&typeof v==='object'){
   for(const name of SUBSTRATES)if(typeof v.growth?.[name]==="number"&&v.growth[name]>=0.25&&v.growth[name]<=2)state.growth[name]=v.growth[name];
   for(const name of BIOMES)if(typeof v.biome?.[name]==="number"&&v.biome[name]>=0&&v.biome[name]<=3)state.biome[name]=v.biome[name];
   if(Number.isInteger(v.revision))state.revision=v.revision;
  }
 }catch{state={growth:{},biome:{},revision:0};}
 return state;
}
export function getLocalTuning(){const s=load();return {growth:{...s.growth},biome:{...s.biome},revision:s.revision};}
export function substrateMultiplier(id){const key=String(id).replace(/^minecraft:/,'');return load().growth[key]??1;}
export function biomeMultiplier(id){
 const str=String(id||'').replace(/^minecraft:/,'').toLowerCase();
 const exact=BIOMES.find(n=>str===n)||BIOMES.find(n=>str.includes(n));
 return exact?(load().biome[exact]??1):1;
}
export function setLocalTuning(group,name,value,expectedRev){
 const s=load(), keys=group==='growth'?SUBSTRATES:group==='biome'?BIOMES:null;
 if(!keys||!keys.includes(name)||s.revision!==expectedRev)return false;
 const min=group==='growth'?0.25:0,max=group==='growth'?2:3;
 if(typeof value!=="number"||!Number.isFinite(value)||value<min||value>max)return false;
 const next={growth:{...s.growth},biome:{...s.biome},revision:s.revision+1};
 if(value===1)delete next[group][name];else next[group][name]=value;
 try{world.setDynamicProperty(KEY,JSON.stringify(next));state=next;return true;}catch{return false;}
}
