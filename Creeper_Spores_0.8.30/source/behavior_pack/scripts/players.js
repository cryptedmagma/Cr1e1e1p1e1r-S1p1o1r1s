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
import { hasSporeProtection, protectionPieces } from "./protection.js";

const carry = new Map();
const armorContact = new Map();            // playerId -> { strain, left, expires }
let runs = 0;

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
          if (cfg.carriersEnabled && strain !== STRAIN_INDEX.royal && protectionPieces(p) < 4) {
            carry.set(p.id, { strain, left: 3, expires: now + 2400 });
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
      const c = carry.get(p.id);
      if (c) {
        if (!cfg.carriersEnabled || now > c.expires || c.left <= 0) {
          carry.delete(p.id);
          try { p.setDynamicProperty("cs:carried_strain", undefined); } catch {}
        }
        else if (runs % 5 === 0 && Math.random() < cfg.carrierChance) {
          const v = p.getVelocity();
          if (v.x * v.x + v.z * v.z > 0.0025 && tryDeposit(dim, p.location, c.strain)) c.left--;
        }
      }
    } catch { /* player left or changed dimension mid-scan */ }
  }
  if (armorContact.size > 1000) armorContact.clear();
  if (carry.size) {
    const online = new Set(world.getAllPlayers().map(p => p.id));
    for (const id of [...carry.keys()]) if (!online.has(id)) carry.delete(id);   // disconnects drop pending carry state
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
