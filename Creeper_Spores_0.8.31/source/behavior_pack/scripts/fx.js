import { world } from "@minecraft/server";

// Per-player cosmetic preferences. These NEVER touch gameplay results: they only decide
// whether a given player is shown/played a particle or sound.
const KEY = "cs:prefs";
export const PREF_DEFAULTS = { sounds: true, particles: 2 /* 0 off, 1 reduced, 2 full */ };

export function getPrefs(player) {
  try {
    const raw = player.getDynamicProperty(KEY);
    if (typeof raw === "string") {
      const p = JSON.parse(raw);
      return {
        sounds: typeof p.sounds === "boolean" ? p.sounds : true,
        particles: [0, 1, 2].includes(p.particles) ? p.particles : 2,
      };
    }
  } catch { /* fall through */ }
  return { ...PREF_DEFAULTS };
}
export function setPrefs(player, prefs) {
  try { player.setDynamicProperty(KEY, JSON.stringify({ sounds: !!prefs.sounds, particles: [0, 1, 2].includes(prefs.particles) ? prefs.particles : 2 })); return true; } catch { return false; }
}

function nearby(dim, loc, r) { try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch { return []; } }

/** Plays a sound to each nearby player who has sounds enabled. Failure is silent by design. */
export function sound(dim, id, loc, { volume = 1, pitch = 1, range = 24 } = {}) {
  for (const p of nearby(dim, loc, range)) {
    try { if (getPrefs(p).sounds) p.playSound(id, { location: loc, volume, pitch }); } catch { /* missing asset / player left */ }
  }
}

/** Spawns a particle once per call, only if at least one nearby player wants particles. Reduced mode skips 2 of 3 cues. */
let reducedTick = 0;
export function particle(dim, id, loc, { range = 32, essential = false } = {}) {
  let full = false, reduced = false;
  for (const p of nearby(dim, loc, range)) {
    const lvl = getPrefs(p).particles;
    if (lvl === 2) full = true; else if (lvl === 1) reduced = true;
  }
  if (!full && !(reduced && (essential || (++reducedTick % 3 === 0)))) return;
  try { dim.spawnParticle(id, loc); } catch { /* missing particle definition: visual fallback is "nothing" */ }
}

/** Combined cue. */
export function cue(dim, loc, { snd, particles, essential = false, volume, pitch } = {}) {
  if (snd) sound(dim, snd, loc, { volume, pitch });
  if (particles) for (const id of Array.isArray(particles) ? particles : [particles]) particle(dim, id, loc, { essential });
}
