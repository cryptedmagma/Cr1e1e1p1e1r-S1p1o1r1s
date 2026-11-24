import { world, system } from "@minecraft/server";
import {
  SPORE_BLOCK, STATE_AGE, STATE_STRAIN, getBlockSafe, belowOf, isFree, isSpore, hasSupport,
  getBiomeId, isSurvivalLike,
} from "./util.js";
import { STRAINS } from "./generated_data.js";
import { STRAIN_INDEX } from "./logic.js";
import { getConfig } from "./config.js";
import { addPending } from "./spores.js";
import { record } from "./journal.js";
import { diag } from "./diag.js";
import { hasSporeProtection, protectionPieces } from "./protection.js";

const carry = new Map();                   // playerId -> { strain, left, remaining }
const armorContact = new Map();
let runs = 0;
// 0.8.31: player carrier state is saved on the player and its window counts down in active
// ticks, so leaving and reloading the world no longer silently drops a carried spore.
export const PLAYER_CARRY = "cs:player_carry_0831";
export const PLAYER_CARRY_TICKS = 2400;
export function decodePlayerCarry(raw) {
  try {
    const c = typeof raw === "string" ? JSON.parse(raw) : null;
    if (!c || !Number.isInteger(c.strain) || c.strain < 0 || c.strain > 7) return null;
    if (!Number.isInteger(c.left) || c.left <= 0 || !Number.isFinite(c.remaining) || c.remaining <= 0) return null;
    return { strain: c.strain, left: Math.min(3, c.left), remaining: Math.min(PLAYER_CARRY_TICKS, c.remaining) };
  } catch { return null; }
}
// Spectators pass through blocks and never touch pods, so they never become carriers.
export function isSpectator(p) {
  try { return String(p.getGameMode()).toLowerCase() === "spectator"; } catch { return false; }
}
function saveCarry(p, c) {
  try { p.setDynamicProperty(PLAYER_CARRY, c ? JSON.stringify(c) : undefined); } catch {}
}
function loadCarry(p) {
  if (carry.has(p.id)) return carry.get(p.id);
  let c = null;
  try { c = decodePlayerCarry(p.getDynamicProperty(PLAYER_CARRY)); } catch {}
  if (c) carry.set(p.id, c);
  return c;
}
function dropCarry(p) {
  carry.delete(p.id);
  saveCarry(p, null);
  try { p.setDynamicProperty("cs:carried_strain", undefined); } catch {}
}

function playerContactSpore(dim, location) {
  const x=Math.floor(location.x),y=Math.floor(location.y),z=Math.floor(location.z);
  const here=getBlockSafe(dim,{x,y,z});
  if(isSpore(here))return here;
  const below=getBlockSafe(dim,{x,y:y-1,z});
  return isSpore(below)?below:undefined;
}

export function tryDeposit(dim, loc, strain) {
  const cfg = getConfig();
  const b = getBlockSafe(dim, { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) });
  if (!b || !isFree(b) || isSpore(b) || !hasSupport(belowOf(b))) return false;
  if (cfg.deepDarkBlocksNatural) {
    const biome = getBiomeId(dim, loc);
    if (typeof biome === "string" && biome.includes("deep_dark")) return false;
  }
  return addPending(dim, b.location, strain);
}

// Players brushing past swollen pods pick up spores and drop them elsewhere; toxic pods poison.
system.runInterval(() => {
  runs++;
  const cfg = getConfig();
  const now = system.currentTick;
  for (const p of world.getPlayers()) {
    try {
      const dim = p.dimension;
      const here = playerContactSpore(dim, p.location);
      if (isSpore(here)) {
        const age = here.permutation.getState(STATE_AGE);
        const strain = here.permutation.getState(STATE_STRAIN) ?? 0;
        if (age >= 3) {
          record(p, "strain", STRAINS[strain]?.key);
          if (dim.id.includes("nether")) record(p, "visit", "nether"); else if (dim.id.includes("the_end")) record(p, "visit", "end");
          if (strain === STRAIN_INDEX.toxic && isSurvivalLike(p) && !hasSporeProtection(p) && !p.getEffect("poison")) p.addEffect("poison", 80, { amplifier: 0 });
          if (cfg.carriersEnabled && strain !== STRAIN_INDEX.royal && protectionPieces(p) < 4 && !isSpectator(p)) {
            const fresh = { strain, left: 3, remaining: PLAYER_CARRY_TICKS };
            carry.set(p.id, fresh);
            saveCarry(p, fresh);
            try { p.setDynamicProperty("cs:carried_strain", strain); } catch {}
          }
        }
      }
      // Armor-contact is an independent route. It is OFF by default and
      // cannot use a complete four-piece protective suit as a carrier.
      if(cfg.advancedTransport && cfg.armoredCarrierTransport && cfg.carriersEnabled &&
         protectionPieces(p)>0 && protectionPieces(p)<4 &&
         (armorContact.get(p.id)??-99999)+160<=now){
        const residue=p.getDynamicProperty("cs:carried_strain");
        if(Number.isInteger(residue) && residue>=0 && residue<8 &&
           Math.random()<cfg.transportChance && tryDeposit(dim,p.location,residue)){
          armorContact.set(p.id,now);
        }
      }
      const c = loadCarry(p);
      if (c) {
        c.remaining -= 20; // this loop runs every 20 ticks
        if (!cfg.carriersEnabled || c.remaining <= 0 || c.left <= 0) dropCarry(p);
        else {
          if (runs % 5 === 0 && Math.random() < cfg.carrierChance) {
            const v = p.getVelocity();
            if (v.x * v.x + v.z * v.z > 0.0025 && tryDeposit(dim, p.location, c.strain)) c.left--;
          }
          if (c.left <= 0) dropCarry(p); else if (runs % 5 === 0) saveCarry(p, c);
        }
      }
    } catch { /* player left or changed dimension mid-scan */ }
  }
  if (armorContact.size > 1000) armorContact.clear();
  if (carry.size) {
    const online = new Set(world.getAllPlayers().map(p => p.id));
    for (const id of [...carry.keys()]) if (!online.has(id)) carry.delete(id);   // in-memory only; the saved copy reloads on rejoin
  }

  // hatchlings shed spores near their feet (bounded per run)
  if (runs % 5 === 0) {
    for (const dimId of ["overworld", "nether", "the_end"]) {
      let list = [];
      try { list = world.getDimension(dimId).getEntities({ families: ["cs_spore_creeper"] }); } catch { continue; }
      let n = 0;
      for (const e of list) {
        if (n++ >= 40) break;
        try {
          if (Math.random() < cfg.shedChance) {
            const s = e.getDynamicProperty("cs:strain");
            tryDeposit(e.dimension, e.location, typeof s === "number" ? s : 0);
          }
        } catch { /* entity removed */ }
      }
    }
  }
}, 20);

// 0.8.31: a player who dies while carrying spores releases the carried strain where they fell
// (nearest supported free cell, never into quarantine via addPending), then stops carrying.
const PLAYER_DEATH_OFFSETS = [[0,0,0],[0,1,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,-1,0],[0,-2,0]];
world.afterEvents.entityDie.subscribe((ev) => {
  try {
    const p = ev.deadEntity;
    if (p?.typeId !== "minecraft:player") return;
    const c = loadCarry(p);
    if (!c) return;
    const cfg = getConfig();
    const dim = p.dimension, at = p.location;
    dropCarry(p);
    if (!cfg.carriersEnabled) return;
    system.run(() => {
      for (const [dx, dy, dz] of PLAYER_DEATH_OFFSETS) {
        try {
          if (tryDeposit(dim, { x: at.x + dx, y: at.y + dy, z: at.z + dz }, c.strain)) {
            diag("player_spore_death_released", { strain: c.strain }); return;
          }
        } catch {}
      }
      // Void, lava or quarantine: nothing valid nearby. The carrier is still cleared (one attempt only).
      diag("player_spore_death_no_valid_cell", { strain: c.strain });
    });
  } catch { /* player data unavailable during death */ }
});

// /scriptevent cs:carrier — read-only inspection of your own carrier state and nearby infected mobs.
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== "cs:carrier") return;
  const p = ev.sourceEntity;
  if (p?.typeId !== "minecraft:player") return;
  try {
    const c = loadCarry(p);
    p.sendMessage(c ? `§eYou carry strain ${c.strain}: ${c.left} deposit(s) left, ${Math.ceil(c.remaining / 20)}s of carried time left.`
                    : "§7You are not carrying spores.");
    let n = 0;
    for (const e of p.dimension.getEntities({ location: p.location, maxDistance: 16, tags: ["cs_spore_carrier"] })) {
      if (n++ >= 8) break;
      let info = "unreadable";
      try {
        const m = JSON.parse(e.getDynamicProperty("cs:mob_spore_061") ?? "null");
        if (m) info = `strain ${m.strain}, ${(m.distance ?? 0).toFixed(1)} blocks walked, ${Math.round((m.activeTicks ?? 0) / 20)}s carried, drip ${m.dripped ? "done" : m.dripRolled ? "rolled" : "pending"}`;
      } catch {}
      p.sendMessage(`§a${e.typeId.replace("minecraft:", "")}§r: ${info}`);
    }
    if (!n) p.sendMessage("§7No infected mobs within 16 blocks.");
  } catch { p.sendMessage("§cCarrier inspection failed."); }
});
