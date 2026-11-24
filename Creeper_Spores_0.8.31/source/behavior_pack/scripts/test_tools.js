// Explicit in-world QA helpers. These run only on /scriptevent commands.
// Use a disposable world for cs:test_blast: the fuse can damage nearby blocks.
import { world } from "@minecraft/server";
import { getBlockSafe, belowOf, isFree, hasSupport, isSpore, STATE_AGE, STATE_STRAIN } from "./util.js";
import { plantSpore, knownPods } from "./spores.js";
import { STRAINS } from "./generated_data.js";
import { diag } from "./diag.js";

const TEST_STRAIN_COUNT=8;
const FIXTURE_OFFSETS=[];
for(let r=2;r<=6;r++){
  for(let x=-r;x<=r;x++)for(let z=-r;z<=r;z++){
    if(Math.max(Math.abs(x),Math.abs(z))!==r)continue;
    if((x+z+r*2)%2===0)FIXTURE_OFFSETS.push({x,z});
  }
}
// The command is useful even when the player is flying above the spawn area.
// Scan nearby candidate heights downward before a few heights above the player.
const FIXTURE_HEIGHTS=[0,...Array.from({length:32},(_,i)=>-(i+1)),1,2,3];
const FIXTURE_SITES=[];
for(const y of FIXTURE_HEIGHTS)for(const off of FIXTURE_OFFSETS)FIXTURE_SITES.push({x:off.x,y,z:off.z});

export function placeStrainFixture(player){
  const dim=player.dimension,origin={x:Math.floor(player.location.x),y:Math.floor(player.location.y),z:Math.floor(player.location.z)};
  let placed=0,cursor=0;
  for(let strain=0;strain<TEST_STRAIN_COUNT;strain++){
    let success=false;
    while(cursor<FIXTURE_SITES.length&&!success){
      const off=FIXTURE_SITES[cursor++],pos={x:origin.x+off.x,y:origin.y+off.y,z:origin.z+off.z};
      const block=getBlockSafe(dim,pos);
      if(!block||!isFree(block)||!hasSupport(belowOf(block)))continue;
      try{plantSpore(block,strain);placed++;success=true;}catch{}
    }
  }
  diag("runtime_strain_fixture",{placed,expected:TEST_STRAIN_COUNT,x:origin.x,y:origin.y,z:origin.z});
  player.sendMessage(`§bCreeper Spores test: placed ${placed}/${TEST_STRAIN_COUNT} stage-0 strains on valid nearby ground.`);
  return placed;
}

export function forceVanillaBlast(player){
  const loc=player.location,dim=player.dimension;
  const spawn={x:Math.floor(loc.x)+4.5,y:Math.floor(loc.y),z:Math.floor(loc.z)+0.5};
  try{
    const creeper=dim.spawnEntity("minecraft:creeper",spawn);
    creeper.triggerEvent("minecraft:start_exploding");
    diag("runtime_blast_fixture_started",{typeId:creeper.typeId,x:Math.floor(spawn.x),y:Math.floor(spawn.y),z:Math.floor(spawn.z)});
    player.sendMessage("§cTest Creeper ignited. Move away; use only in a disposable world. Check nearby ground for a larger, visible stage-3 spore after the blast.");
    return true;
  }catch(e){
    diag("runtime_blast_fixture_failed",{err:String(e).slice(0,100)});
    player.sendMessage("§cCould not force the test Creeper. See /scriptevent cs:diag for the failure.");
    return false;
  }
}

/** Reports the actual nearby pods seen by the block-tick registry, grouped by strain and visible age. */
export function inspectNearbySpores(player){
  const dim=player.dimension;
  const pods=knownPods(dim.id,player.location,64,2000);
  const counts=Array.from({length:STRAINS.length},()=>Array(8).fill(0));
  let checked=0;
  for(const pod of pods){
    const block=getBlockSafe(dim,pod);
    if(!isSpore(block))continue;
    const strain=Number(block.permutation.getState(STATE_STRAIN)??0);
    const age=Number(block.permutation.getState(STATE_AGE)??0);
    if(!Number.isInteger(strain)||strain<0||strain>=counts.length||!Number.isInteger(age)||age<0||age>7)continue;
    counts[strain][age]++;checked++;
  }
  diag("runtime_spore_inspection",{nearby:checked,registered:pods.length});
  if(!checked){
    player.sendMessage("§eNo nearby spore pods have ticked yet. Run cs:test_spores, wait 2 seconds, then run cs:inspect_spores again.");
    return counts;
  }
  player.sendMessage(`§bNearby spore ages (0–7), ${checked} pod(s):`);
  for(let strain=0;strain<counts.length;strain++){
    if(!counts[strain].some(n=>n))continue;
    player.sendMessage(`§f${STRAINS[strain]?.name??`Strain ${strain}`}: §a${counts[strain].join(" ")}`);
  }
  return counts;
}

world.afterEvents.scriptEventReceive.subscribe(ev=>{
  if(ev.id!=="cs:test_spores"&&ev.id!=="cs:test_blast"&&ev.id!=="cs:inspect_spores")return;
  const player=ev.sourceEntity;
  if(!player||player.typeId!=="minecraft:player"){
    world.sendMessage("§cRun this test from a player in a disposable Creative world.");
    return;
  }
  if(ev.id==="cs:test_spores")placeStrainFixture(player);
  else if(ev.id==="cs:test_blast")forceVanillaBlast(player);
  else inspectNearbySpores(player);
});
