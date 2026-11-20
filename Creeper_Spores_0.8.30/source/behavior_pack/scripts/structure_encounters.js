// Creeper Spores 0.4.0 — structure-aware nests, gated by a PRE-RELEASE dimension API.
// Never guesses where a vanilla structure is. If detection API is unavailable it does nothing.
import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";
import { getBlockSafe, isFree, hasSupport, getBiomeId, sendActionBar, giveItem } from "./util.js";
import { record } from "./journal.js";
import { diag } from "./diag.js";
import { addPending } from "./spores.js";
const KEY="cs:structure_nests_v1"; let done;
function init(){if(done)return;try{const data=JSON.parse(world.getDynamicProperty(KEY)??"[]");done=new Set(Array.isArray(data)?data.slice(-500):[]);}catch{done=new Set();}}
function save(){try{world.setDynamicProperty(KEY,JSON.stringify([...done].slice(-500)));}catch{diag("nest_registry_save_failed");}}
const types=["village","temple","pyramid","ruin","shipwreck","fortress","bastion","mineshaft","stronghold","monument","city","trial_chamber","igloo","hut","outpost"];
let playerCursor=0;
system.runInterval(()=>{
  const cfg=getConfig();if(!cfg.structureNests)return;
  init();const players=world.getPlayers();if(!players.length)return;
  const player=players[playerCursor++%players.length],dim=player.dimension;
  if(typeof dim.getGeneratedStructures!=="function") {if(playerCursor%40===0)diag("structure_query_api_unavailable");return;}
  const loc=player.location;
  let found=[];try{found=dim.getGeneratedStructures(loc).map(String).filter(s=>types.some(t=>s.includes(t)));}catch{return;}
  if(!found.length)return;
  const cx=Math.floor(loc.x/32),cz=Math.floor(loc.z/32),kind=found[0];
  const k=`${dim.id}:${cx}:${cz}:${kind}`;if(done.has(k))return;
  // A verified structure alone is not permission to replace existing terrain or loot chests.
  let best;
  for(let i=0;i<6;i++){
    const x=Math.floor(loc.x)+Math.floor(Math.random()*11)-5, z=Math.floor(loc.z)+Math.floor(Math.random()*11)-5;
    const y=Math.floor(loc.y)+Math.floor(Math.random()*5)-2;
    const at=getBlockSafe(dim,{x,y,z});
    if(at&&at.isAir&&hasSupport(getBlockSafe(dim,{x,y:y-1,z}))){best=at;break;}
  }
  if(!best)return;
  const b=getBiomeId(dim,best.location);
  if(cfg.deepDarkBlocksNatural && typeof b==="string"&&b.includes("deep_dark"))return;
  try{best.setType("cookiedookie:spore_nest");done.add(k);save();diag("structure_nest_created",{kind});}
  catch{diag("structure_nest_placement_failed");}
},200);

world.beforeEvents.playerInteractWithBlock.subscribe(ev=>{
  try {
    if(ev.block?.typeId!=="cookiedookie:spore_nest")return;
    ev.cancel=true;
    const p=ev.player,dim=ev.block.dimension,pos={...ev.block.location};
    system.run(()=>{
      const b=getBlockSafe(dim,pos); if(b?.typeId!=="cookiedookie:spore_nest")return;
      b.setType("minecraft:air");  // commit the pickup BEFORE spawning rewards
      giveItem(p,"cookiedookie:nest_fragment",1);
      if(Math.random()<0.2)giveItem(p,"cookiedookie:luminous_shard",1);
      record(p,"scan");
      record(p,"nest");
      // Villagers at verified village encounters may expose dedicated, non-vanilla spore trades.
      try {
        const cfg=getConfig();
        const structures=dim.getGeneratedStructures?.(pos)??[];
        if(cfg.traderEncounters && structures.some(s=>String(s).includes("village")) && Math.random()<0.35)
          dim.spawnEntity("cookiedookie:spore_trader",{x:pos.x+.5,y:pos.y,z:pos.z+.5});
      }catch{diag("trader_spawn_unavailable");}
      sendActionBar(p,"§aYou uncovered a Creeper Spore Nest!");
      if(Math.random()<0.2) addPending(dim,{x:pos.x+1,y:pos.y,z:pos.z},0);
    });
  } catch{}
});
