CREEPER SPORES 0.8.0 - IMPLEMENTATION REPORT
Minecraft Bedrock Edition only. Experimental. Updated 2026-11-19.

WHAT WAS ACTUALLY ADDED OR CHANGED
1. Connected-colony graph: bounded graph of loaded, recently observed, genuine spore pods. Links within 7 blocks, reports connected groups to the Colony Map, never forces chunk loading.
2. Optional network growth cooperation: networks of three or more pods can advance one eligible connected pod per scheduled scan, with a per-scan cap. OFF by default.
3. 23 creeper environmental ability profiles: each named variant can receive an environment-specific temporary self-effect (speed, resistance, regeneration, night vision, etc.). No direct changes to creeper attacks or explosions. OFF by default.
4. 23 new low-amplitude ambient head animations, one per named creeper, with existing 3D textures and geometry preserved.
5. Three hybrid plant blocks with four actual stage geometries apiece: Spore Bluebell (luminous), Spore Bracken (common) and Spore Bogcap (toxic). Each has its own pixel-art texture, growth callback and non-duplicating harvest. OFF by default.
6. Three hybrid harvest items and three recipes: Luminescent Berry, Fungal Fiber and Marsh Cap.
7. Optional designed, five-piece spore micro-ruins: center nest, two lanterns and two moss-carpet accents, placed only in inspected empty locations on suitable surfaces. OFF by default. Not a full vanilla structure template.
8. Player-placed terrain tracking from THIS UPDATE forward: helps exclude known placed blocks from optional infection and optional ruin construction. Bound to a maximum of 600 recorded locations and saved on a timer. It CANNOT identify blocks placed before this update, via commands, or by unrelated add-ons.
9. Six additional earned research milestones for hybrid plant collection, nests, atlas reading, connected networks and variant discovery. Genuine callbacks record events and prevent repeated reward payment.
10. Expanded Colony Map showing locally connected loaded-colony groups alongside historical last-seen coordinates. This is a text UI, not a native map item displaying live icons on a rendered atlas.
11. New independently saved administrator switches: colonyNetworks, networkCooperation, variantEcology, hybridPlants and fieldRuins. New world-mutating systems start OFF.
12. Separate OPTIONAL native Bedrock feature-rules pack for rare Spore Nest placement in newly generated forest, plains, taiga and jungle areas. NOT included in the default active add-on. This is a draft based on the documented feature-rule schema and requires Bedrock testing. It is a distinct worldgen path from the configurable local worldgen code.
13. A new 0.8.0 offline regression suite, source archive, and installable Bedrock .mcaddon composed of separate behavior and resource .mcpack archives.

UNCHANGED ON PURPOSE
- All 23 creeper entity identifiers, model geometry and reference texture files stay intact.
- Original 23 artwork references still included in the master ZIP.
- Existing spores stages 0-7, strains 0-7, spawning rules and pod-hatching rules stay intact.
- Stage-1 pickup of spores by eligible living mobs, 15-block 40% one-time drip WITHOUT cleansing, final 20 blocks + 40 ticks successful deposit WITH cleansing, and spore release upon death stay intact.
- All 11 lightweight infection visual types, no attached creeper-like spore bud.
- Existing air-cloud, fluid-route, item, vehicle and portal-spreading logic retained.
- Main pack UUIDs remain the same; both manifests advance from 0.7.0 to 0.8.0.

INSTALLATION
1. BACK UP YOUR WORLD first. Experimental add-on; no in-game Bedrock test has been run here.
2. Import Creeper_Spores_0.8.0_Expanded.mcaddon. It contains separate behavior/resource .mcpack archives.
3. Enable BOTH Creeper Spores packs for your world. Use an appropriate Bedrock build that meets min_engine_version 1.21.130 and supports the beta Script APIs declared in the manifest.
4. New world-changing systems are independently OFF by default. Use Research Journal > Advanced Settings to enable hybridPlants, fieldRuins, networkCooperation or variantEcology as desired.
5. Only if you explicitly WANT native generation in newly made chunks, import and activate Creeper_Spores_0.8.0_OPTIONAL_Native_Worldgen.mcpack alongside the core add-on. This worldgen is NOT controlled by the core in-game naturalGeneration toggle; disable the optional pack to disable the feature rule. It is NOT a replacement for structure validation. Keep backup worlds.
6. If .mcaddon fails to import on your device, import Creeper_Spores_0.8.0_Behavior.mcpack and Creeper_Spores_0.8.0_Resources.mcpack separately and activate both.

VERIFICATION DONE IN THIS ENVIRONMENT
- 0.8.0 JSON documents parse, JavaScript modules pass Node syntax checks.
- Static imports resolve; new custom block components, model files, textures, items, recipes, identifiers, and manifest pairings are checked.
- 23 original creeper behavior entity files, model geometry files and actual skin textures compare byte-for-byte against 0.7.0.
- Existing mob-carrier and old spore-airflow JS files compare byte-for-byte against 0.7.0.
- Basic connected graph behavior checked in an offline Node VM.
- Both .mcpack files, the .mcaddon and full archive receive ZIP integrity checks.
- THIS DOES NOT PROVE Bedrock gameplay compatibility. No Bedrock client, Realm, mobile device or server was launched here.

STILL NOT IMPLEMENTED OR NOT FINISHED (DO NOT MARK COMPLETED)
A. Full unique, non-passive AI for all 23 creepers: variant-exclusive target choice, movement pathing, attacks, explosions and drops. 0.8 adds contextual self-effects only, not complete AI.
B. Complete water/lava/phantom navigation under Bedrock collision and current physics.
C. Fluid-accurate underwater currents and rain runoff, genuine wind airflow and environment-fidelity physics.
D. Full collision-aware leaf and vine transport, natural cave airflow, all item/vehicle/portal transfer edge cases.
E. World-spanning, persistent synchronized colony networks and full coordinated colony AI. The new graph observes only loaded nearby pods, and cooperative tick is optional.
F. Custom hybrid plants for every requested vanilla crop and biome. Only three new hybrids are created; full withering, crop suppression, cross-pollination, all harvest products, and all approved special cases are not done.
G. Distinct geometry/textures for infected animals and hostile mobs. These were deliberately not added due to the selected lightweight visual mode.
H. Full species-specific mob attraction, avoidance, reactions, and infection visuals for every model type.
I. Integrating spore trades into ordinary vanilla villager professions. The separate research trader remains.
J. Full .mcstructure templates, authentic special-structure chambers, procedural jigsaw structures, bespoke traps, and all special structure rewards. Only a small opt-in scripted micro-ruin is added.
K. Guaranteed natural world generation across all agreed biomes. Optional sidecar feature rules are a limited proof-of-concept and not independently tested in Minecraft.
L. A real drawn, persistent colonization atlas or native map overlay (the Colony Map is a text survey).
M. Full narrative quest-lines, branching story, dialogue, and every requested progression reward. Six additional measurable milestones are included.
N. Industrial-scale redstone factories, complex storage routing and robust automation compatibility.
O. Physical opening of the original spore block with real changing collision; separate shell effect still used.
P. Unique, fully authored birth animations for all 23 creepers. The new 23 animations are subtle ambient head movements, not full hatch scenes.
Q. Finished specialized audio/animated particles for all events and all mob types.
R. Truly custom thrown grenade projectile model and fully verified impact physics (current snowball carrier).
S. Complete protective armor wearable appearance (current definitions not full new wearable models).
T. Final detailed models for spore lantern/torch and ornamental infected blocks; full infected material list.
U. True protection of all existing player-made structures; only new player placement tracking exists, is capped, and cannot reconstruct historical block origins.
V. Exact biome spawn and substrate growth multipliers where earlier Yes/No choices directly conflict; neutral defaults are preserved rather than guessing.
W. Absolute guarantees about every item, crafting recipe, trade, controller mode or new component: files and logic exist but in-game function is not proven.
X. Bedrock compatibility for custom blocks, 23 ambient animations, three new hybrid block components, optional feature rules, all sound and particle names, and feature APIs is not proven.
Y. Actual visual inspection of all 23 3D models and hybrid blocks in Bedrock, texture correctness, particle density, and performance on mobile/controller.
Z. Live migration and persistence tests for older saved worlds (0.1-0.7), multiplayer/Realm races, dedicated server, and long-running colonies.

All unrun acceptance tests from 0.7.0 remain UNRUN. No in-game test is treated as passed by the offline suite. The supplemental 0.8 test plan lists the new acceptance cases.
