import { world, system } from "@minecraft/server";
import { diag } from "./diag.js";

// Schema 3 = micro-spore values stored as "<dueAbsoluteTime>:<strain>" strings.
// Legacy 0.1.0 values are negative numbers of ticks still to wait; they are rewritten ONCE, preserving remaining time.
// Anything unrecognised is left untouched (never deleted) and counted in diagnostics.
const SCHEMA_KEY = "cs:schema";
export const SCHEMA = 3;
const KEY_RE = /^spores\.([^(]+)\((-?\d+),\s*(-?\d+),\s*(-?\d+)\)$/;

export function migrate() {
  const result = { converted: 0, skipped: 0, already: false };
  try {
    if (world.getDynamicProperty(SCHEMA_KEY) === SCHEMA) { result.already = true; return result; }
    const now = world.getAbsoluteTime();
    for (const id of world.getDynamicPropertyIds()) {
      if (!id.startsWith("spores.")) continue;
      if (!KEY_RE.test(id)) { result.skipped++; diag("migrate_bad_key", { id: id.slice(0, 60) }); continue; }
      const v = world.getDynamicProperty(id);
      if (typeof v === "number") {
        world.setDynamicProperty(id, `${now + Math.abs(Math.round(v))}:0`);
        result.converted++;
      } else if (typeof v === "string" && /^\d+:\d+$/.test(v)) { /* already current */ }
      else { result.skipped++; diag("migrate_bad_value", { id: id.slice(0, 60) }); }
    }
    world.setDynamicProperty(SCHEMA_KEY, SCHEMA);   // only after the loop: a crash mid-way simply re-runs it safely
  } catch (e) { diag("migrate_error", { err: String(e).slice(0, 80) }); }
  return result;
}
