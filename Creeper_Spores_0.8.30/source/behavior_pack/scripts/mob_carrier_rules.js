// Creeper Spores 0.6.3: all living mob species can be spore carriers. Original 0.6.2 travel/release rules retained.
// Pure calculation functions are intentionally separate from the Bedrock runtime.
export const CARRY_TAG = "cs_spore_carrier";
export const CARRY_STATE = "cs:mob_spore_061"; // KEEP original key for old-world migration.
export const CLEAN_UNTIL = "cs:mob_clean_until_061";
export const CARRY_DURATION = 2400;
export const CARRY_SCAN_MAX = 64;
export const CARRY_SCAN_RADIUS = 32;
export const CARRY_GLOBAL_SCAN_BUDGET = 256;
// These are nonliving technical entities, not mobs. Every other entity with a health
// component is eligible, including vanilla bosses, villagers, aquatic mobs, mobs
// introduced by other add-ons, and ALL 23 of our creeper variants.
export const NON_MOB_TYPES = new Set([
  "minecraft:player", "minecraft:armor_stand", "minecraft:npc", "minecraft:item",
  "minecraft:xp_orb", "minecraft:boat", "minecraft:chest_boat", "minecraft:minecart",
  "minecraft:chest_minecart", "minecraft:hopper_minecart", "minecraft:tnt_minecart",
  "minecraft:command_block_minecart", "minecraft:spawner_minecart", "minecraft:arrow",
  "minecraft:snowball", "minecraft:egg", "minecraft:trident", "minecraft:ender_pearl",
  "minecraft:fireball", "minecraft:small_fireball", "minecraft:dragon_fireball",
  "minecraft:shulker_bullet", "minecraft:wither_skull", "minecraft:wind_charge",
  "minecraft:breeze_wind_charge", "minecraft:fireworks_rocket", "minecraft:area_effect_cloud",
  "minecraft:lightning_bolt", "minecraft:falling_block", "minecraft:painting",
  "minecraft:item_frame", "minecraft:glow_item_frame", "minecraft:leash_knot",
  "minecraft:ender_crystal", "minecraft:interaction", "minecraft:fishing_hook",
  "cookiedookie:spore_shell"
]);
// Pure eligibility rule, separate from the runtime component check for offline tests.
export function isLivingMobType(typeId, hasHealth) {
  return typeof typeId === "string" && typeId.length > 0 &&
    !NON_MOB_TYPES.has(typeId) && hasHealth === true;
}
export function mayCarrySpore(entity) {
  try { return isLivingMobType(entity.typeId, entity.hasComponent("minecraft:health")); }
  catch { return false; }
}

// A mob must actually stand on/touch a spore. Do not infect one from a neighbouring block.
export const SOURCE_OFFSETS = Object.freeze([[0,0,0],[0,-1,0]]);
export const LANDING_OFFSETS = Object.freeze([[0,0,0],[0,1,0],[0,-1,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]]);
export const DEATH_LANDING_OFFSETS = Object.freeze([...LANDING_OFFSETS,
  [0,-2,0],[0,-3,0],[1,-1,0],[-1,-1,0],[0,-1,1],[0,-1,-1],
  [1,-2,0],[-1,-2,0],[0,-2,1],[0,-2,-1]]);
export function groundPoint(p) { return {x:Math.floor(p.x), y:Math.floor(p.y), z:Math.floor(p.z)}; }
export function makeCarrier(strain, pos, now, dimension) {
  if(!Number.isInteger(strain)||strain<0||strain>7) return null;
  if(!pos||![pos.x,pos.y,pos.z].every(Number.isFinite)) return null;
  const p={x:pos.x,y:pos.y,z:pos.z};
  return {strain, origin:groundPoint(pos), acquired:now, expires:now+CARRY_DURATION,
    dimension, lastPosition:p, lastDimension:dimension, distance:0,
    dripRolled:false, dripApproved:false, dripped:false};
}
export function validCarrier(c, now) {
  return !!c && Number.isInteger(c.strain) && c.strain>=0 && c.strain<=7 &&
    Number.isFinite(c.acquired) && Number.isFinite(c.expires) && now>=c.acquired && now<=c.expires &&
    !!c.origin && [c.origin.x,c.origin.y,c.origin.z].every(Number.isFinite);
}
// Old-world 0.6.1 carriers lack distance fields. Retain their strain and remaining expiry.
export function upgradeCarrier(c, pos, dimension) {
  if(!c || !pos) return c;
  if(!Number.isFinite(c.distance) || c.distance<0) c.distance=0;
  if(!c.lastPosition || ![c.lastPosition.x,c.lastPosition.y,c.lastPosition.z].every(Number.isFinite))
    c.lastPosition={x:pos.x,y:pos.y,z:pos.z};
  if(!c.lastDimension) c.lastDimension=dimension;
  if(typeof c.dripRolled!=='boolean') c.dripRolled=false;
  if(typeof c.dripApproved!=='boolean') c.dripApproved=false;
  if(typeof c.dripped!=='boolean') c.dripped=false;
  return c;
}
// Count distance ALONG the sampled walking path, rather than only displacement from the pod.
// Teleports and dimension changes do not manufacture spore travel; unloaded mobs never force-load chunks.
export function progressCarrier(c, pos, dimension) {
  upgradeCarrier(c,pos,dimension);
  const p=c.lastPosition;
  const length=Math.hypot(pos.x-p.x,pos.y-p.y,pos.z-p.z);
  if(c.lastDimension===dimension && Number.isFinite(length) && length>0 && length<=16)
    c.distance+=length;
  c.lastPosition={x:pos.x,y:pos.y,z:pos.z};
  c.lastDimension=dimension;
  return c.distance;
}
// Compatibility with older test/util callers: this checks DISPLACEMENT, not the accumulated path.
export function travelEnough(c, pos, min) {
  if(!c||!pos||![pos.x,pos.y,pos.z].every(Number.isFinite))return false;
  const dx=pos.x-c.origin.x,dy=pos.y-c.origin.y,dz=pos.z-c.origin.z;
  return dx*dx+dy*dy+dz*dz >= Math.max(0,min)**2;
}
export function dripEligible(c, cfg) {
  return !c.dripRolled && !c.dripped && (c.distance??0)>=(cfg.mobDripTravelBlocks??15);
}
export function attemptDripRoll(c, cfg, rng=Math.random) {
  if(!dripEligible(c,cfg)) return false;
  c.dripRolled=true;
  c.dripApproved=rng()<(cfg.mobDripChance??0.40);
  return c.dripApproved;
}
export function dropEligible(c, now, pos, cfg) {
  return validCarrier(c,now) && now-c.acquired >= (cfg.mobMinCarryTicks??40) &&
    (c.distance??0)>=(cfg.mobMinTravelBlocks??20);
}
export function releaseResult(deposited) {return deposited?'clean':'carrying';}
