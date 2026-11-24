import { system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { openLocalTuning } from "./tuning_forms.js";
import { STRAINS, VARIANTS } from "./generated_data.js";
import { NS, giveItem } from "./util.js";
import { getConfig, setConfig, resetConfig, resetKeys, exportConfig, importConfig, getRev, isAdmin } from "./config.js";
import { getPrefs, setPrefs } from "./fx.js";
import { formatDiag, clearDiag } from "./diag.js";
import { reapplyMovementSwitches } from "./entities.js";

// ---------------------------------------------------------------------------
// Player-private research progress. These are add-on milestones, not platform achievements.
// ---------------------------------------------------------------------------
const KEY = "cs:journal";

function normalize(j) {
  return {
    strains: Array.isArray(j.strains) ? j.strains : [],
    variants: Array.isArray(j.variants) ? j.variants : [],
    done: Array.isArray(j.done) ? j.done : [],
    scans: j.scans | 0, hatches: j.hatches | 0, harvests: j.harvests | 0, planted: j.planted | 0,
    detects: j.detects | 0, zones: j.zones | 0, purges: j.purges | 0,
    visits: Array.isArray(j.visits) ? j.visits : [],
    hybridHarvests: j.hybridHarvests | 0, nests: j.nests | 0, atlasOpens: j.atlasOpens | 0, networkFinds: j.networkFinds | 0,
    storyStep: Math.max(0, Math.min(10, j.storyStep | 0)),
    storyPath: j.storyPath === "garden" || j.storyPath === "ruins" ? j.storyPath : "",
  };
}
export function getJournal(player) {
  try {
    const raw = player.getDynamicProperty(KEY);
    if (typeof raw === "string") return normalize(JSON.parse(raw));
  } catch { /* corrupt: start fresh */ }
  return normalize({});
}
function save(player, j) { try { player.setDynamicProperty(KEY, JSON.stringify(j)); return true; } catch { return false; } }

export const MILESTONES = [
  { id: "first_sprout", name: "First Sprout", desc: "Plant or scan your first spore.",
    test: j => j.planted + j.scans > 0, prog: j => `${Math.min(1, j.planted + j.scans)}/1`, xp: 5, items: [] },
  { id: "field_biologist", name: "Field Biologist", desc: "Identify 3 different strains.",
    test: j => j.strains.length >= 3, prog: j => `${Math.min(3, j.strains.length)}/3`, xp: 20, items: [["spore_extract", 2]] },
  { id: "hatchery", name: "Hatchery Witness", desc: "Witness 5 hatchings.",
    test: j => j.hatches >= 5, prog: j => `${Math.min(5, j.hatches)}/5`, xp: 15, items: [["hardened_shell", 1]] },
  { id: "taxonomist", name: "Taxonomist", desc: "Witness 5 different creeper variants hatch.",
    test: j => j.variants.length >= 5, prog: j => `${Math.min(5, j.variants.length)}/5`, xp: 40, items: [["luminous_shard", 2]] },
  { id: "harvester", name: "Careful Harvester", desc: "Harvest 10 pods.",
    test: j => j.harvests >= 10, prog: j => `${Math.min(10, j.harvests)}/10`, xp: 15, items: [["volatile_essence", 1]] },
  { id: "royal", name: "Royal Cultivator", desc: "Raise a Royal spore.",
    test: j => j.strains.includes("royal"), prog: j => (j.strains.includes("royal") ? "1/1" : "0/1"), xp: 50, items: [["spore_catalyst", 1]] },
  { id: "complete_strains", name: "Master Cultivator", desc: "Identify all 8 strains.",
    test: j => j.strains.length >= STRAINS.length, prog: j => `${j.strains.length}/${STRAINS.length}`, xp: 100, items: [["spore_catalyst", 2]] },
  { id: "surveyor", name: "Surveyor", desc: "Use a Spore Detector 3 times.",
    test: j => j.detects >= 3, prog: j => `${Math.min(3, j.detects)}/3`, xp: 10, items: [] },
  { id: "quarantine", name: "Quarantine Officer", desc: "Set up a quarantine zone with a Spore Sprayer.",
    test: j => j.zones >= 1, prog: j => `${Math.min(1, j.zones)}/1`, xp: 20, items: [["spore_extract", 2]] },
  { id: "cleanup", name: "Clean-up Crew", desc: "Purify or vacuum growths 3 times.",
    test: j => j.purges >= 3, prog: j => `${Math.min(3, j.purges)}/3`, xp: 15, items: [] },
  { id: "deep_colonies", name: "Beyond the Overworld", desc: "Find a swollen pod in the Nether and in the End.",
    test: j => j.visits.includes("nether") && j.visits.includes("end"),
    prog: j => `${(j.visits.includes("nether") ? 1 : 0) + (j.visits.includes("end") ? 1 : 0)}/2`, xp: 40, items: [["volatile_essence", 1]] },
  { id: "rare_creeper", name: "Rare Hatchling", desc: "Witness a Giant, Miniature or Spore Queen hatch.",
    test: j => ["giant", "miniature", "spore_queen"].some(k => j.variants.includes(k)),
    prog: j => (["giant", "miniature", "spore_queen"].some(k => j.variants.includes(k)) ? "1/1" : "0/1"), xp: 40, items: [["hardened_shell", 2]] },
  { id: "herbalist", name: "Spore Herbalist", desc: "Harvest 3 hybrid plants.",
    test: j=>j.hybridHarvests>=3, prog:j=>`${Math.min(3,j.hybridHarvests)}/3`, xp:20, items:[["spore_pigment",1]] },
  { id: "botanical_scholar", name: "Botanical Scholar", desc: "Harvest 12 hybrid plants.",
    test: j=>j.hybridHarvests>=12, prog:j=>`${Math.min(12,j.hybridHarvests)}/12`, xp:45, items:[["fungal_crystal",1]] },
  { id: "nest_seeker", name: "Nest Seeker", desc: "Open 2 discovered spore nests.",
    test: j=>j.nests>=2, prog:j=>`${Math.min(2,j.nests)}/2`, xp:25, items:[["nest_fragment",2]] },
  { id: "map_reader", name: "Survey Apprentice", desc: "Open your colony map twice.",
    test: j=>j.atlasOpens>=2, prog:j=>`${Math.min(2,j.atlasOpens)}/2`, xp:10, items:[] },
  { id: "network_discovery", name: "Network Biologist", desc: "Survey one connected colony with three or more pods.",
    test: j=>j.networkFinds>=1, prog:j=>`${Math.min(1,j.networkFinds)}/1`, xp:30, items:[["glowing_thread",1]] },
  { id: "world_biologist", name: "World Biologist", desc: "Identify 10 different creeper variants.",
    test: j=>j.variants.length>=10, prog:j=>`${Math.min(10,j.variants.length)}/10`, xp:80, items:[["spore_catalyst",1]] },
];

/**
 * kind: "strain" | "variant" | "scan" | "plant" | "hatch" | "harvest"
 * Completion is committed (saved) before any reward is handed out, so an overlapping
 * callback or a reconnect can never pay the same milestone twice.
 */
export function record(player, kind, value) {
  try {
    const j = getJournal(player);
    if (kind === "strain" && value && !j.strains.includes(value)) j.strains.push(value);
    else if (kind === "variant" && value && !j.variants.includes(value)) j.variants.push(value);
    else if (kind === "scan") { j.scans++; if (value && !j.strains.includes(value)) j.strains.push(value); }
    else if (kind === "plant") { j.planted++; if (value && !j.strains.includes(value)) j.strains.push(value); }
    else if (kind === "hatch") { j.hatches++; if (value && !j.variants.includes(value)) j.variants.push(value); }
    else if (kind === "harvest") j.harvests++;
    else if (kind === "detect") j.detects++;
    else if (kind === "zone") j.zones++;
    else if (kind === "purge") j.purges++;
    else if (kind === "hybrid") j.hybridHarvests++;
    else if (kind === "nest") j.nests++;
    else if (kind === "atlas") j.atlasOpens++;
    else if (kind === "network") j.networkFinds++;
    else if (kind === "visit" && value && !j.visits.includes(value)) j.visits.push(value);

    const fresh = MILESTONES.filter(m => !j.done.includes(m.id) && m.test(j));
    for (const m of fresh) j.done.push(m.id);
    if (!save(player, j)) return;
    for (const m of fresh) {
      try { if (m.xp) player.addExperience(m.xp); } catch { /* xp is cosmetic-adjacent; item rewards still follow */ }
      for (const [item, n] of m.items) giveItem(player, `${NS}:${item}`, n);
      try { player.sendMessage(`§a[Spore Journal]§r Milestone: §e${m.name}§r — ${m.desc}`); player.playSound("cookiedookie.sting"); } catch { /* notification only */ }
    }
  } catch { /* progression must never break gameplay */ }
}

// ---------------------------------------------------------------------------
// Forms
// ---------------------------------------------------------------------------
async function show(form, player) {
  for (let i = 0; i < 10; i++) {
    const r = await form.show(player);
    if (!(r.canceled && r.cancelationReason === "UserBusy")) return r;
    await new Promise(res => system.runTimeout(res, 10));
  }
  return { canceled: true };
}

export async function openJournal(player) {
  try {
    const j = getJournal(player);
    const admin = isAdmin(player);
    const f = new ActionFormData().title("Spore Research Journal")
      .body(`Strains identified: ${j.strains.length}/${STRAINS.length}\nVariants witnessed: ${j.variants.length}/${Object.keys(VARIANTS).length}\nScans: ${j.scans}   Hatchings: ${j.hatches}   Harvests: ${j.harvests}`)
      .button("Strain Encyclopedia").button("Creeper Roster").button("Milestones").button("My Preferences");
    if (admin) f.button("World Settings").button("Mutation Settings").button("Creeper Features").button("Advanced Settings").button("Config Export / Import").button("Diagnostics").button("Local Growth & Biome Rates");
    f.button("Field Story");
    const r = await show(f, player);
    if (r.canceled) return;
    if (r.selection === 0) return page(player, "Strain Encyclopedia", STRAINS.map(s =>
      j.strains.includes(s.key) ? `§a${s.name}§r\n${s.info}` : "§8??? Unidentified strain§r").join("\n\n"));
    if (r.selection === 1) return openRoster(player, j);
    if (r.selection === 2) return page(player, "Milestones", MILESTONES.map(m =>
      `${j.done.includes(m.id) ? "§a[x]" : "§7[ ]"} ${m.name}§r — ${m.desc}${j.done.includes(m.id) ? "" : ` (${m.prog(j)})`}`).join("\n"));
    if (r.selection === 3) return openPrefs(player);
    if (admin && r.selection === 4) return openSettings(player);
    if (admin && r.selection === 5) return openMutation(player);
    if (admin && r.selection === 6) return openFeatures(player);
    if (admin && r.selection === 7) return openAdvanced(player);
    if (admin && r.selection === 8) return openTransfer(player);
    if (admin && r.selection === 9) return openDiagnostics(player);
    if (admin && r.selection === 10) return openLocalTuning(player);
    if (r.selection === (admin ? 11 : 4)) return openStory(player);
  } catch { /* UI is informational only */ }
}

// A compact branching research story built from existing, saved journal events.
// Chapter rewards are committed to the player's saved progress before XP is granted.
const STORY_CHAPTERS = [
  { title: "The Sleeping Spore", text: "A faint pulse answers your first sample. The colony is alive, but its language is unknown.", ready: j => j.planted + j.scans >= 1, progress: j => `${Math.min(1, j.planted + j.scans)}/1 sample`, xp: 5 },
  { title: "A Spectrum in the Mist", text: "Different strains carry different signals. Compare three before drawing conclusions.", ready: j => j.strains.length >= 3, progress: j => `${Math.min(3, j.strains.length)}/3 strains`, xp: 10 },
  { title: "The First Hatch", text: "The pod opens. A new creeper emerges, and the field notes gain their first living subject.", ready: j => j.hatches >= 1, progress: j => `${Math.min(1, j.hatches)}/1 hatch`, xp: 15 },
  { title: "The Field Study", text: "Choose what to study next: cultivate new hybrid growths, or investigate discovered nests.", ready: () => true, progress: () => "Choose a research path", xp: 0 },
  { title: "A Living Network", text: "Garden Path: document twelve hybrid harvests. Ruin Path: find two nests and survey a connected colony.", ready: j => j.storyPath === "garden" ? j.hybridHarvests >= 12 : j.nests >= 2 && j.networkFinds >= 1,
    progress: j => j.storyPath === "garden" ? `${Math.min(12, j.hybridHarvests)}/12 hybrid harvests` : `${Math.min(2, j.nests)}/2 nests; ${Math.min(1, j.networkFinds)}/1 network`, xp: 35 },
  { title: "Field Notes in Bloom", text: "The spores answer differently in every habitat. Compare enough strains to recognize the pattern beneath their colors.", ready: j => j.strains.length >= 5, progress: j => `${Math.min(5, j.strains.length)}/5 identified strains`, xp: 20 },
  { title: "The Unfamiliar Face", text: "A mature colony can produce more than one kind of Creeper. Record several hatchlings before deciding what the colony is becoming.", ready: j => j.hatches >= 5 && j.variants.length >= 5, progress: j => `${Math.min(5, j.hatches)}/5 hatchings; ${Math.min(5, j.variants.length)}/5 variants`, xp: 30 },
  { title: "A Path Through the Roots", text: "Garden Path: gather twenty hybrid harvests and document the plants that sustain the colony. Ruin Path: open three nests and connect their clues to a surveyed colony.", ready: j => j.storyPath === "garden" ? j.hybridHarvests >= 20 : j.nests >= 3 && j.networkFinds >= 1,
    progress: j => j.storyPath === "garden" ? `${Math.min(20, j.hybridHarvests)}/20 hybrid harvests` : `${Math.min(3, j.nests)}/3 nests; ${Math.min(1, j.networkFinds)}/1 network`, xp: 40 },
  { title: "Beyond the Familiar World", text: "The trail does not end at the edge of the Overworld. Visit both distant dimensions and compare what survived the crossing.", ready: j => j.visits.includes("nether") && j.visits.includes("end"), progress: j => `${(j.visits.includes("nether") ? 1 : 0) + (j.visits.includes("end") ? 1 : 0)}/2 dimensions surveyed`, xp: 35 },
  { title: "Keeper of the Record", text: "Complete the field record: identify every strain, document ten Creeper variants, and make ten scans. Your notes now describe a living system rather than a single outbreak.", ready: j => j.strains.length >= STRAINS.length && j.variants.length >= 10 && j.scans >= 10,
    progress: j => `${Math.min(STRAINS.length, j.strains.length)}/${STRAINS.length} strains; ${Math.min(10, j.variants.length)}/10 variants; ${Math.min(10, j.scans)}/10 scans`, xp: 100 },
];

async function openStory(player) {
  const j = getJournal(player), step = j.storyStep;
  if (step >= STORY_CHAPTERS.length) return page(player, "Field Story — Complete", "Your field record is complete. The colony's origins remain open for future discoveries.");
  if (step === 3 && !j.storyPath) {
    const f = new ActionFormData().title("Choose a Field Study")
      .body("This choice changes the objectives in the final chapters. It does not change world generation or other players' progress.")
      .button("Garden Path\nHarvest hybrid plants")
      .button("Ruin Path\nExplore spore nests");
    const r = await show(f, player);
    if (r.canceled) return;
    j.storyPath = r.selection === 0 ? "garden" : "ruins";
    j.storyStep = 4;
    if (!save(player, j)) { player.sendMessage("§cYour story choice could not be saved; please open the journal again."); return; }
    player.sendMessage(`§aField study chosen: ${j.storyPath === "garden" ? "Garden Path" : "Ruin Path"}.`);
    return openStory(player);
  }
  const ch = STORY_CHAPTERS[step];
  const pathLabel = j.storyPath === "garden" ? "Garden Path" : j.storyPath === "ruins" ? "Ruin Path" : "Not chosen";
  const title = step === 4 ? (j.storyPath === "garden" ? "Garden Path — " : "Ruin Path — ") + ch.title : ch.title;
  const f = new ActionFormData().title(title)
    .body(`${ch.text}\n\nResearch path: ${pathLabel}\nObjective: ${ch.progress(j)}\n\nChapter ${step + 1} of ${STORY_CHAPTERS.length}`);
  if (ch.ready(j)) f.button(step === 3 ? "Choose a path" : "Complete chapter");
  f.button("Back");
  const r = await show(f, player);
  if (r.canceled || r.selection !== 0 || !ch.ready(j)) return openJournal(player);
  if (step === 3) return openStory(player);
  j.storyStep++;
  if (!save(player, j)) { player.sendMessage("§cChapter progress could not be saved; no reward was granted."); return; }
  try { if (ch.xp) player.addExperience(ch.xp); } catch { /* progress is already committed */ }
  try { player.playSound("cookiedookie.sting"); } catch { /* notification only */ }
  player.sendMessage(`§a[Field Story]§r ${ch.title} complete. +${ch.xp} XP`);
  return openStory(player);
}

async function page(player, title, body) {
  const f = new ActionFormData().title(title).body(body).button("Back");
  const r = await show(f, player);
  if (!r.canceled) return openJournal(player);
}

const NUM = [
  ["infectionVisualQuality", "Infection visuals (0 off, 1 light, 2 full)", 0, 2, 1],
  ["infectionVisualRange", "Infection visual distance (blocks)", 8, 32, 1],
  ["depositChance", "Spore landing chance per block", 0, 1, 0.01],
  ["radiusNormal", "Creeper blast spore radius", 1, 12, 1],
  ["radiusCharged", "Charged creeper spore radius", 1, 16, 1],
  ["maxPlacementsPerBlast", "Max seeds per blast", 1, 100, 1],
  ["growthAdvanceChance", "Growth speed (1 = normal, lower = slower)", 0.05, 1, 0.05],
  ["mutationChance", "Mutation chance", 0, 1, 0.01],
  ["variantChance", "Variant hatch chance (common strain)", 0, 1, 0.01],
  ["maxCreepersNear", "Creeper limit near a pod", 1, 32, 1],
  ["harvestYield", "Harvest yield multiplier", 0, 4, 0.25],
];
const BOOL = [
  ["infectionVisuals", "Show green slime, stains, mushrooms and spores"],
  ["hatchEnabled", "Pods can hatch creepers"],
  ["barriersEnabled", "Barriers block spore spread"],
  ["carriersEnabled", "Players/mobs can carry spores"],
  ["deepDarkBlocksNatural", "No natural spores in the Deep Dark"],
];

async function openSettings(player) {
  const cfg = getConfig();
  const rev = getRev();
  const f = new ModalFormData().title("Creeper Spores Settings");
  for (const [k, label, lo, hi, step] of NUM) f.slider(label, lo, hi, { valueStep: step, defaultValue: Math.min(hi, Math.max(lo, cfg[k])) });
  for (const [k, label] of BOOL) f.toggle(label, { defaultValue: cfg[k] });
  f.toggle("Restore all defaults", { defaultValue: false });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;            // cancel commits nothing
  if (!isAdmin(player)) { player.sendMessage("§cYou no longer have permission to change settings."); return; }
  if (getRev() !== rev) { player.sendMessage("§cSettings were changed by someone else while this form was open. Reopen it."); return; } // re-check at submit
  const v = r.formValues;
  if (v[NUM.length + BOOL.length] === true) { resetConfig(); player.sendMessage("§aSpore settings restored to defaults."); return; }
  const patch = {};
  NUM.forEach(([k], i) => { patch[k] = Number(v[i]); });
  BOOL.forEach(([k], i) => { patch[k] = !!v[NUM.length + i]; });
  player.sendMessage(setConfig(patch) ? "§aSpore settings saved." : "§cNo valid changes; settings unchanged.");
}

// ---- roster with full-body portraits ----------------------------------------
async function openRoster(player, j) {
  const entries = Object.entries(VARIANTS);
  const f = new ActionFormData().title("Creeper Roster").body("Hatch a variant to unlock its entry.");
  for (const [k, v] of entries) {
    if (j.variants.includes(k)) f.button(v.name, `textures/${NS}/portraits/${k}`);   // missing icon just shows no image
    else f.button("§8???");
  }
  f.button("Back");
  const r = await show(f, player);
  if (r.canceled) return;
  if (r.selection >= entries.length) return openJournal(player);
  const [k, v] = entries[r.selection];
  if (!j.variants.includes(k)) return openRoster(player, j);
  const s = STRAINS[v.strain];
  const move = v.move ? `\nMovement: ${v.move === "water" ? "swims" : v.move === "lava" ? "walks through lava" : "hovers and flies"} (switchable)` : "";
  const d = new ActionFormData().title(v.name).body(`Origin strain: ${s.name}${move}`).button("Back", `textures/${NS}/portraits/${k}`);
  const rr = await show(d, player);
  if (!rr.canceled) return openRoster(player, j);
}

// ---- admin: mutation settings (edits live only in the form until submitted) ---
const MUT = [[1, "Luminous"], [2, "Toxic"], [3, "Frost"], [4, "Ember"], [5, "Aqua"], [6, "Sculk"]];

async function openMutation(player) {
  const cfg = getConfig();
  const rev = getRev();
  const f = new ModalFormData().title("Mutation Settings");
  f.slider("Mutation chance", 0, 1, { valueStep: 0.01, defaultValue: cfg.mutationChance });
  for (const [i, name] of MUT) f.toggle(`Allow ${name} mutations`, { defaultValue: ((cfg.mutationOutcomes >> i) & 1) === 1 });
  f.toggle("Restore mutation defaults", { defaultValue: false });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;                    // cancel: saved values untouched
  if (!isAdmin(player)) { player.sendMessage("§cYou no longer have permission to change settings."); return; }
  if (getRev() !== rev) { player.sendMessage("§cSettings were changed by someone else while this form was open. Reopen it."); return; }
  const v = r.formValues;
  if (v[1 + MUT.length] === true) { setConfig({ mutationChance: 0.10, mutationOutcomes: 126 }); player.sendMessage("§aMutation settings restored."); return; }
  let mask = 0;
  MUT.forEach(([i], n) => { if (v[1 + n]) mask |= 1 << i; });
  player.sendMessage(setConfig({ mutationChance: Number(v[0]), mutationOutcomes: mask }) ? "§aMutation settings saved. Applies to future growth and blasts." : "§cNo valid changes.");
}

// ---- admin: feature switches ------------------------------------------------
const FEATS = [
  ["waterMovement", "Water creeper swimming"], ["lavaMovement", "Lava creeper lava-walking"],
  ["phantomMovement", "Phantom creeper flight"], ["hatchAnimation", "Hatch animation sequence"],
  ["emergenceStages", "Newborn growth stages"], ["debugDiagnostics", "Detailed diagnostics log"],
];
async function openFeatures(player) {
  const cfg = getConfig();
  const rev = getRev();
  const f = new ModalFormData().title("Creeper Features");
  for (const [k, label] of FEATS) f.toggle(label, { defaultValue: cfg[k] });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;
  if (!isAdmin(player)) { player.sendMessage("§cYou no longer have permission to change settings."); return; }
  if (getRev() !== rev) { player.sendMessage("§cSettings were changed by someone else while this form was open. Reopen it."); return; }
  const patch = {};
  FEATS.forEach(([k], i) => { patch[k] = !!r.formValues[i]; });
  if (setConfig(patch)) {
    const n = reapplyMovementSwitches();                      // reversible: flips already-spawned creepers too
    player.sendMessage(`§aFeatures saved. Updated ${n} loaded creeper${n === 1 ? "" : "s"}.`);
  } else player.sendMessage("§cNo valid changes.");
}

async function openDiagnostics(player) {
  const f = new ActionFormData().title("Spore Diagnostics").body(formatDiag(10)).button("Back").button("Clear counters");
  const r = await show(f, player);
  if (r.canceled) return;
  if (r.selection === 1 && isAdmin(player)) { clearDiag(); player.sendMessage("§aDiagnostics cleared."); }
  return openJournal(player);
}

// ---- per-player cosmetic preferences (never change gameplay) ------------------
async function openPrefs(player) {
  const p = getPrefs(player);
  const f = new ModalFormData().title("My Preferences")
    .toggle("Spore sounds", { defaultValue: p.sounds })
    .dropdown("Spore particles", ["Off", "Reduced", "Full"], { defaultValueIndex: p.particles });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;
  setPrefs(player, { sounds: !!r.formValues[0], particles: Number(r.formValues[1]) });
  player.sendMessage("§aPreferences saved. These only change what you see and hear.");
}

// ---- admin: advanced / remaining settings ----------------------------------
const ADV_NUM = [
  ["germinationMinTicks", "Germination min (ticks)", 20, 24000, 20],
  ["germinationMaxTicks", "Germination max (ticks)", 20, 48000, 20],
  ["maxPendingSpores", "Max pending microspores", 100, 20000, 100],
  ["carrierChance", "Player carrier deposit chance", 0, 1, 0.01],
  ["mobDripChance", "Mob drip chance after 15 blocks", 0, 1, 0.01],
  ["shedChance", "Hatchling shed chance", 0, 1, 0.01],
  ["spreadChance", "Colony spread chance", 0, 1, 0.01],
  ["colonySize", "Colony size cap", 1, 64, 1],
  ["controllerCooldown", "Controller cooldown (ticks)", 10, 1200, 10],
  ["transportChance", "Advanced transport chance", 0, 1, 0.01],
  ["airCloudSpawnChance", "Air cloud launch chance", 0, 0.4, 0.01],
  ["airCloudSettleChance", "Air cloud settle chance", 0, 1, 0.01],
  ["airCloudMaxActive", "Active airborne cloud limit", 8, 96, 8],
  ["infectionChance", "Terrain infection chance", 0, 0.5, 0.01],
  ["naturalSpawnChance", "Natural generation chance per scanned cell", 0, 0.5, 0.01],
  ["incubatorInterval", "Incubator ticks per stage", 20, 2400, 20],
];
const ADV_BOOL = [
  ["spreadEnabled", "Colonies spread sideways"], ["cropEcology", "Pods affect nearby crops"],
  ["mobEcology", "Mobs trample/carry spores"], ["redstoneControllers", "Spore Controllers active"],
  ["zonesEnabled", "Quarantine zones active"],
  ["advancedTransport", "Advanced transmission routes"],
  ["airClouds", "Moving airborne spore clouds"],
  ["waterCurrentRouting", "Neighbouring liquid-flow-aware transport"],
  ["waterTransport", "Water transmission"],
  ["caveAirTransport", "Cave-air transmission (approximation)"],
  ["splashPotionTransport", "Spore-carrying splash potions"],
  ["armoredCarrierTransport", "Armor-contact carriers (not full suits)"],
  ["rainTransport", "Rain-runoff transmission"],
  ["windTransport", "Wind-gust transmission"],
  ["vineTransport", "Vine transmission"],
  ["leafTransport", "Falling-leaf transmission"],
  ["itemTransport", "Dropped-item carriers"],
  ["vehicleTransport", "Boat and minecart carriers"],
  ["portalTransport", "Portal carrier deposits"],
  ["terrainInfection", "Reversible terrain infection (changes blocks)"],
  ["ornamentalInfection", "Infect logs/leaves/wool/glass (extra opt-in)"],
  ["naturalGeneration", "Add natural spores to loaded regions"],
  ["structureNests", "Structure nests (pre-release API)"],
  ["traderEncounters", "Spore traders near discovered village nests"],
  ["plantEcology", "Additional plant ecology"],
  ["mobReactions", "Additional mob reactions"],
  ["villagerReactions", "Villager warning sounds"],
  ["incubatorsEnabled", "Spore incubators"],
  ["colonyNetworks", "Scan connected loaded colonies"],
  ["networkCooperation", "Colony growth cooperation (changes pods)"],
  ["variantEcology", "Creeper variant environmental abilities"],
  ["hybridPlants", "Hybrid plants (places custom growths)"],
  ["fieldRuins", "Surface spore micro-ruins (new structures)"],
];
async function openAdvanced(player) {
  const cfg = getConfig(), rev = getRev();
  const f = new ModalFormData().title("Advanced Settings");
  for (const [k, label, lo, hi, step] of ADV_NUM) f.slider(label, lo, hi, { valueStep: step, defaultValue: Math.min(hi, Math.max(lo, cfg[k])) });
  for (const [k, label] of ADV_BOOL) f.toggle(label, { defaultValue: cfg[k] });
  f.toggle("Restore ONLY the settings on this page to defaults", { defaultValue: false });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;
  if (!isAdmin(player)) { player.sendMessage("§cYou no longer have permission to change settings."); return; }
  if (getRev() !== rev) { player.sendMessage("§cSettings were changed by someone else while this form was open. Reopen it."); return; }
  const v = r.formValues, nb = ADV_NUM.length;
  if (v[nb + ADV_BOOL.length] === true) { resetKeys([...ADV_NUM, ...ADV_BOOL].map(x => x[0])); player.sendMessage("§aThese settings were restored to defaults."); return; }
  const patch = {};
  ADV_NUM.forEach(([k], i) => { patch[k] = Number(v[i]); });
  ADV_BOOL.forEach(([k], i) => { patch[k] = !!v[nb + i]; });
  player.sendMessage(setConfig(patch) ? "§aAdvanced settings saved. Pending tasks keep their old timing; new ones use these values." : "§cNo valid changes.");
}

// ---- admin: export / import (JSON text) ---------------------------------------
async function openTransfer(player) {
  const rev = getRev();
  const f = new ModalFormData().title("Config Export / Import")
    .textField("Current configuration (copy this to export)", "", { defaultValue: exportConfig() })
    .textField("Paste a configuration here to import", "{...}", { defaultValue: "" });
  const r = await show(f, player);
  if (r.canceled || !r.formValues) return;
  const text = String(r.formValues[1] ?? "").trim();
  if (!text) return;
  if (!isAdmin(player)) { player.sendMessage("§cYou no longer have permission to change settings."); return; }
  if (getRev() !== rev) { player.sendMessage("§cSettings were changed by someone else while this form was open. Reopen it."); return; }
  const n = importConfig(text);
  player.sendMessage(n ? `§aImported ${n} setting(s). Invalid or unknown entries were ignored.` : "§cNothing valid to import; settings unchanged.");
}
