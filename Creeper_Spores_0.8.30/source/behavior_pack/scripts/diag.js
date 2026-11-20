import { world, system } from "@minecraft/server";
import { getConfig } from "./config.js";

// Failure diagnostics: counters are always kept and persisted (so reasons survive reloads);
// a detailed ring buffer is kept in memory while debugDiagnostics is on.
const KEY = "cs:diag";
const ring = [];
let counts = null;
let dirty = false;

function load() {
  if (counts) return;
  counts = {};
  try {
    const raw = world.getDynamicProperty(KEY);
    if (typeof raw === "string") counts = JSON.parse(raw) || {};
  } catch { counts = {}; }
}

/** code: short snake_case reason, e.g. "hatch_no_headroom". info: small plain object. */
export function diag(code, info) {
  try {
    load();
    counts[code] = (counts[code] || 0) + 1;
    dirty = true;
    if (getConfig().debugDiagnostics) {
      ring.push({ t: system.currentTick, code, info });
      if (ring.length > 40) ring.shift();
    }
  } catch { /* diagnostics must never affect gameplay */ }
}

export function getDiag() { load(); return { counts: { ...counts }, recent: [...ring] }; }
export function clearDiag() {
  load(); counts = {}; ring.length = 0; dirty = true;
  try { world.setDynamicProperty(KEY, undefined); } catch { /* ignore */ }
}

export function formatDiag(maxRecent = 8) {
  const { counts: c, recent } = getDiag();
  const lines = Object.entries(c).sort((a, b) => b[1] - a[1]).map(([k, n]) => `${k}: ${n}`);
  const tail = recent.slice(-maxRecent).map(r => `t${r.t} ${r.code} ${r.info ? JSON.stringify(r.info) : ""}`);
  return (lines.length ? lines.join("\n") : "No rejections recorded.") + (tail.length ? "\n\nRecent:\n" + tail.join("\n") : "");
}

system.runInterval(() => {
  if (!dirty) return;
  dirty = false;
  try { world.setDynamicProperty(KEY, JSON.stringify(counts)); } catch { dirty = true; }
}, 600);

system.afterEvents.scriptEventReceive.subscribe(ev => {
  try {
    if (ev.id !== "cs:diag" && ev.id !== "cs:diag_clear") return;
    const target = ev.sourceEntity && typeof ev.sourceEntity.sendMessage === "function" ? ev.sourceEntity : world;
    if (ev.id === "cs:diag_clear") { clearDiag(); target.sendMessage("§aSpore diagnostics cleared."); return; }
    target.sendMessage("§e[Spore diagnostics]§r\n" + formatDiag(10));
  } catch { /* ignore */ }
});
