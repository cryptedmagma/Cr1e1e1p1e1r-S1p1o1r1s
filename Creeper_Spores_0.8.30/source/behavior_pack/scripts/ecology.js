import { world, system, ItemStack } from "@minecraft/server";
import {
  SPORE_BLOCK, STATE_AGE, STATE_STRAIN, getBlockSafe, belowOf, isFree, isSpore, hasSupport, blockedBetween, getBiomeId,
} from "./util.js";
import { STRAIN_INDEX } from "./logic.js";
import { getConfig } from "./config.js";
import { podHooks, addPending } from "./spores.js";
import { inZone } from "./zones.js";
import { plantSpore } from "./spores.js";
import { CARRY_TAG, CARRY_STATE, CLEAN_UNTIL, CARRY_SCAN_MAX, CARRY_SCAN_RADIUS, CARRY_GLOBAL_SCAN_BUDGET, mayCarrySpore, SOURCE_OFFSETS, LANDING_OFFSETS, DEATH_LANDING_OFFSETS, groundPoint, makeCarrier, validCarrier, upgradeCarrier, progressCarrier, dripEligible, attemptDripRoll, dropEligible } from "./mob_carrier_rules.js";
import { diag } from "./diag.js";
import { renderCarrier, carrierCleaned, sporeShedding, deathShedding, VISUAL_BUDGET } from "./infection_visuals.js";

// ---------------------------------------------------------------------------
// Colony spread: mature pods (age >= 5) seed nearby ground, capped by local colony size.
// ---------------------------------------------------------------------------
function countPodsNear(dim, b, r) {
  let n = 0;
  for (let x = -r; x <= r; x++) for (let z = -r; z <= r; z++) for (let y = -1; y <= 1; y++) {
    const o = getBlockSafe(dim, { x: b.x + x, y: b.y + y, z: b.z + z });
    if (o && isSpore(o)) n++;
  }
  return n;
}

function spread(block, strain, cfg) {
  const dim = block.dimension;
  if (countPodsNear(dim, block, 4) >= cfg.colonySize) { diag("spread_colony_full"); return; }
  const dx = Math.floor(Math.random() * 5) - 2, dz = Math.floor(Math.random() * 5) - 2, dy = Math.floor(Math.random() * 3) - 1;
  if (!dx && !dz) return;
  const t = getBlockSafe(dim, { x: block.x + dx, y: block.y + dy, z: block.z + dz });
  if (!t || !isFree(t) || isSpore(t) || !hasSupport(belowOf(t))) return;
  if (cfg.barriersEnabled && blockedBetween(dim, block.location, t.location, 6)) { diag("spread_barrier"); return; }
  addPending(dim, t.location, strain);            // addPending itself rejects quarantined cells, duplicates and a full queue
}

// ---------------------------------------------------------------------------
// Crop ecology: reads the crop's CURRENT growth state at execution time; never kills or replaces a crop.
//  - toxic pods set crops back one stage (rarely); other non-frost, non-ember strains nudge them forward.
// ---------------------------------------------------------------------------
const CROPS = new Set(["minecraft:wheat", "minecraft:carrots", "minecraft:potatoes", "minecraft:beetroot"]);
function crops(block, strain) {
  const dim = block.dimension;
  let done = 0;
  for (let x = -2; x <= 2 && done < 3; x++) for (let z = -2; z <= 2 && done < 3; z++) {
    const b = getBlockSafe(dim, { x: block.x + x, y: block.y, z: block.z + z });
    if (!b || !CROPS.has(b.typeId)) continue;
    const g = b.permutation.getState("growth");
    if (typeof g !== "number") continue;
    if (strain === STRAIN_INDEX.toxic) {
      if (Math.random() < 0.15 && g > 0) { b.setPermutation(b.permutation.withState("growth", g - 1)); done++; }
    } else if (strain !== STRAIN_INDEX.frost && strain !== STRAIN_INDEX.ember) {
      if (Math.random() < 0.2 && g < 7) { b.setPermutation(b.permutation.withState("growth", g + 1)); done++; }
    }
  }
}

podHooks.push((block, age, strain, cfg) => {
  if (cfg.spreadEnabled && age >= 5 && Math.random() < cfg.spreadChance) spread(block, strain, cfg);
  if (cfg.cropEcology && age >= 4) crops(block, strain);
});

// ---------------------------------------------------------------------------
// Mob ecology: age-1+ spores attach when a mob steps on their block.
// From pickup: a single 40% drip roll at 15 blocks of cumulative travel (carrier stays attached);
// one guaranteed FINAL placement on eligible ground after 20 blocks AND 40 ticks (then clean);
// a dying carrier deposits immediately, ignoring distance/time, with item fallback if blocked.
// Existing saved strain and key are preserved; unloaded chunks are never force-loaded.
// ---------------------------------------------------------------------------
// No species blacklist: passive, hostile, neutral, aquatic, flying, boss and
// custom-creeper mobs can all carry spores if they have a health component.
// Players retain their own independent carrier mechanic in players.js.
let scanPlayerCursor=0;
const scanMobCursor = new Map();
const memoryCarry = new Map(); // runtime fallback when entity dynamic properties unavailable
const memoryClean = new Map();
const lastKnown = new Map(); // safe death-position fallback when deadEntity.location is unavailable
const handledDeaths = new Set();

function clearMob(e, now, cfg) {
  carrierCleaned(e,cfg);
  memoryCarry.delete(e.id);
  const until=now + (cfg.mobPickupImmunityTicks ?? 200);
  memoryClean.set(e.id,until);
  try { e.setDynamicProperty(CARRY_STATE, undefined); } catch {}
  try { e.setDynamicProperty(CLEAN_UNTIL,until); } catch {}
  try { e.removeTag(CARRY_TAG); } catch {}
}
function cleanUntil(e) {
  try { const n=e.getDynamicProperty(CLEAN_UNTIL); if(typeof n === 'number')return n; } catch {}
  return memoryClean.get(e.id) ?? 0;
}
function readCarry(e) {
  try {
    const raw=e.getDynamicProperty(CARRY_STATE);
    if(typeof raw==='string') {
      const c=JSON.parse(raw);
      return c && typeof c==='object' ? c : null;
    }
  } catch {}
  return memoryCarry.get(e.id) ?? null;
}
function writeCarry(e,c) {
  memoryCarry.set(e.id,c);
  try { e.setDynamicProperty(CARRY_STATE,JSON.stringify(c)); } catch {}
  try { e.addTag(CARRY_TAG); } catch {}
}
function podTouch(e,cfg) {
  const at=groundPoint(e.location),dim=e.dimension;
  for (const [dx,dy,dz] of SOURCE_OFFSETS) {
    const b=getBlockSafe(dim,{x:at.x+dx,y:at.y+dy,z:at.z+dz});
    if (!isSpore(b))continue;
    const age=b.permutation.getState(STATE_AGE);
    if(age===0 && dx===0 && dy===0 && dz===0 && Math.random()<0.3) {
      b.setType('minecraft:air'); diag('mob_trampled_seed'); return null;
    }
    if(age >= (cfg.mobPickupAge ?? 1)) {
      const strain=b.permutation.getState(STATE_STRAIN) ?? 0;
      return {strain, origin:b.location};
    }
  }
  return null;
}
function depositAt(dim, location, c, isDeath=false) {
  const at=groundPoint(location);
  const offsets=isDeath?DEATH_LANDING_OFFSETS:LANDING_OFFSETS;
  for (const [dx,dy,dz] of offsets) {
    const p={x:at.x+dx,y:at.y+dy,z:at.z+dz};
    const b=getBlockSafe(dim,p);
    if(!b || isSpore(b) || !b.isAir || !hasSupport(belowOf(b)))continue;
    // A carried spore can grow in any valid location, including a cave.
    if(inZone(dim.id,p))continue;
    try {
      plantSpore(b,c.strain);
      diag(isDeath?'mob_spore_death_planted':'mob_spore_dropped_visible',
        {where:dim.id,strain:c.strain});
      return true;
    } catch {diag('mob_spore_drop_failed');}
  }
  return false;
}
function dropVisibleSpore(e,c) {return depositAt(e.dimension,e.location,c);}
function rememberLocation(e,c) {
  const p=e.location, d=e.dimension.id;
  lastKnown.set(e.id,{location:{x:p.x,y:p.y,z:p.z},dimension:d,carry:c});
}
function deathSporeItem(dim,position,c) {
  try {
    const stack=new ItemStack('cookiedookie:creeper_spores',1);
    // ItemStack dynamic properties are optional across API versions; the visual drop remains.
    try {stack.setDynamicProperty('cs:carried_strain',c.strain);}catch{}
    dim.spawnItem(stack,{x:position.x,y:position.y+0.25,z:position.z});
    diag('mob_spore_death_item',{strain:c.strain});
    return true;
  }catch{diag('mob_spore_death_fallback_failed');return false;}
}
// Dead entities may invalidate their location/property APIs, so snapshot both while alive.
// This event is death-specific: an unloaded/removed living mob does not drop a spore.
world.afterEvents.entityDie.subscribe(ev=>{
  try {
    const e=ev.deadEntity;
    const id=e.id;
    if(handledDeaths.has(id))return;
    if(!mayCarrySpore(e) && !lastKnown.has(id))return;
    let c=readCarry(e);
    const snap=lastKnown.get(id);
    if(!c)c=snap?.carry;
    if(!c || !Number.isInteger(c.strain) || c.strain<0 || c.strain>7)return;
    const cfg=getConfig();
    if(!cfg.mobEcology||!cfg.carriersEnabled||!cfg.mobDropOnce)return;
    let loc=snap?.location,dimid=snap?.dimension;
    try {const live=e.location; if(live && [live.x,live.y,live.z].every(Number.isFinite))loc={...live};}catch{}
    try {dimid=e.dimension.id;}catch{}
    if(!loc||!dimid)return;
    handledDeaths.add(id);
    memoryCarry.delete(id); lastKnown.delete(id);memoryClean.delete(id);
    const carrier={strain:c.strain};
    system.run(()=>{
      try {
        const dim=world.getDimension(dimid);
        if(!depositAt(dim,loc,carrier,true))deathSporeItem(dim,loc,carrier);
        deathShedding(dim,loc,cfg);
      }catch{diag('mob_spore_death_drop_error');}
    });
    if(handledDeaths.size>1000)handledDeaths.clear();
  }catch{diag('mob_spore_death_event_error');}
});

system.runInterval(() => {
  try {
    const cfg=getConfig();
    if(!cfg.mobEcology || !cfg.carriersEnabled || !cfg.mobDropOnce) {
      // Do not leave infected indicators stuck on previously seen mobs when disabled.
      for(const p of world.getPlayers()){
        let nearby=[];
        try{nearby=p.dimension.getEntities({location:p.location,maxDistance:16});}catch{}
        for(const e of nearby) if(e.hasTag?.(CARRY_TAG))clearMob(e,world.getAbsoluteTime(),cfg);
      }
      memoryCarry.clear(); return;
    }
    const now=world.getAbsoluteTime();
    const seen=new Set();
    const players=world.getPlayers();
    let globalChecked=0, visualized=0;
    // Rotate the starting player and the starting entity per player so every
    // nearby living species gets scanned even in crowded multiplayer worlds.
    const startPlayer=scanPlayerCursor++;
    for(let pi=0;pi<players.length && globalChecked<CARRY_GLOBAL_SCAN_BUDGET;pi++) {
      const p=players[(startPlayer+pi)%players.length];
      let list=[];
      try { list=p.dimension.getEntities({location:p.location,maxDistance:CARRY_SCAN_RADIUS,
        excludeTypes:["minecraft:player","minecraft:item","minecraft:xp_orb"]}); }
      catch {continue;}
      if(!list.length)continue;
      const start=(scanMobCursor.get(p.id)??0)%list.length;
      const count=Math.min(CARRY_SCAN_MAX,list.length);
      scanMobCursor.set(p.id,(start+count)%list.length);
      for(let i=0;i<count && globalChecked<CARRY_GLOBAL_SCAN_BUDGET;i++) {
        const e=list[(start+i)%list.length];
        if(seen.has(e.id))continue;
        seen.add(e.id);
        globalChecked++;
        if(!mayCarrySpore(e))continue;
        try {
          let c=readCarry(e);
          if(c && !validCarrier(c,now)) {clearMob(e,now,cfg);c=null;}
          // A carrier indicator is purely cosmetic; old worlds may contain
          // an orphaned tag without any saved strain.
          if(!c && e.hasTag(CARRY_TAG)) { try {e.removeTag(CARRY_TAG);}catch{} }
          if(!c) {
            if(now<cleanUntil(e))continue; // post-final-drop clean period
            const touch=podTouch(e,cfg);
            if(touch) {
              c=makeCarrier(touch.strain,e.location,now,e.dimension.id);
              if(c) {
                writeCarry(e,c);rememberLocation(e,c);
                diag('mob_spore_picked_up',{mob:e.typeId,strain:c.strain});
              }
            }
          } else {
            // If the mob doubles back, cumulative movement still counts as walking.
            upgradeCarrier(c,e.location,e.dimension.id);
            progressCarrier(c,e.location,e.dimension.id);
            rememberLocation(e,c);
            // Per-species agnostic, bounded cosmetic infection. No creeper-face bud.
            if(visualized<VISUAL_BUDGET && renderCarrier(e,now,cfg))visualized++;
            // At 15 blocks: ONE 40% roll. A successful drip does not clear the carrier.
            if(dripEligible(c,cfg)) {
              attemptDripRoll(c,cfg);
              diag('mob_spore_drip_rolled',{approved:c.dripApproved});
            }
            if(c.dripApproved && !c.dripped && !dropEligible(c,now,e.location,cfg)) {
              if(dropVisibleSpore(e,c)) {
                c.dripped=true;
                sporeShedding(e.dimension,e.location,cfg);
                diag('mob_spore_dripped_still_carried',{mob:e.typeId});
              }
            }
            // At 20 blocks AND 40 ticks: always attempt final release. No random chance.
            // If no valid ground exists, remain infected and retry at the next scan.
            if(dropEligible(c,now,e.location,cfg) && dropVisibleSpore(e,c)) {
              sporeShedding(e.dimension,e.location,cfg);
              clearMob(e,now,cfg);
              lastKnown.delete(e.id);
              diag('mob_spore_cleaned',{mob:e.typeId});
            } else writeCarry(e,c); // persist progress/roll to survive world reload
          }
        } catch {diag('mob_spore_scan_error');}
      }
    }
    // Bound runtime-only snapshots; saved dynamic properties remain the
    // primary carrier state and persist across world reloads.
    if(memoryCarry.size>2400)memoryCarry.clear();
    if(memoryClean.size>2400)memoryClean.clear();
    if(lastKnown.size>2400)lastKnown.clear();
    if(scanMobCursor.size>200)scanMobCursor.clear();
  } catch {diag('mob_spore_interval_error');}
},20);
