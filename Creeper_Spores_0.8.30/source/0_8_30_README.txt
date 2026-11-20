CREEPER SPORES 0.8.30 — RELIABLE BLAST SEEDING
Minecraft Bedrock Edition only. Experimental. Built from the 0.8.8 source tree.

WHAT CHANGED IN 0.8.30
- The Phantom Creeper wing panels now angle outward and down in five mirrored pairs, giving the model a more ragged, draped silhouette like the supplied reference. Offline geometry checks validate the ten segments and their mirrored rotation data; the in-game silhouette remains unverified.
- The Crystal Creeper model now places a crystal detail on each of its four feet and angles its crown/body shards outward, matching the supplied concept more closely. Offline geometry checks cover the corrected right-foot positions and cube rotations; in-game visual parity still needs review.
- The Spore Controller has a fifth redstone mode, Auto Seed. While powered it queues one new microscopic spore beside a mature colony per cooldown, consumes one Spore Extract from an adjacent inventory, preserves the colony strain, and honors quarantine zones and containment barriers. The existing cooldown and bounded scan keep work finite.
- The four Spore-Proof armor pieces now have player attachables using Bedrock's armor geometry/render controller and separate 64x32 UV-aligned armor textures. Helmet, chest, leggings, and boots map to their matching armor layers. Offline checks validate the item binding and layer geometry; appearance while equipped still needs Minecraft testing.
- All 23 Creeper variants now tune player alert distances, fuse trigger/cancel distances, idle roaming speed, and pursuit speed. Target selectors, swell behavior, nearby sensors, and melee pursuit use consistent per-variant values; existing entity IDs, explosion powers/events, and special-movement groups are preserved. Offline schema assertions check the settings. Bedrock pathing and balance still need gameplay testing.
- The all-strain in-world test command now searches supported ground up to 32 blocks below the player before reporting a placement failure. It still only places on empty/water cells above supported blocks.
- Eligible vanilla and custom Creeper-family explosions now plant at least one larger, clearly visible stage-3 spore on the closest valid nearby surface. Charged explosions seed up to two. This skips the tiny stage-0 fleck and the still-small stage-2 model; ordinary microscopic deposits and manual stage-0 spores keep their original start stage, and blast seeds continue through the regular stage-4 mutation checkpoint.
- The seeds retain the existing strain/mutation rules and honor support checks, containment barriers, quarantine zones, loaded-area checks, and the per-blast placement cap.
- Fixed the 23-variant environmental-ability reader to floor fractional entity coordinates before querying surrounding blocks; which ensures mob positions consistently resolve to their actual block cells. Added a mocked regression check.
- Optional native nest generation now includes eight additional documented Bedrock biome tags: swamp, desert, savanna, mesa/badlands, mangrove swamp, cherry grove, mushroom island, and frozen biomes. This remains a separate, opt-in pack and applies to newly generated chunks only.
- Existing probabilistic microscopic deposits remain as additional spread. These can still add farther colonies after their configured germination delay.
- The before- and after-explosion events are both subscribed. If the before-event has no source, the after-event can still seed; a short cross-phase dedupe window prevents duplicate seeds. Added mocked checks for missing-source fallback and repeat-blast handling. This still requires a Bedrock test.
- Spore pods across all eight strains now tick every 20–40 game ticks (about 1–2 seconds) instead of 300–2,400 ticks, so each stage should become visibly active much sooner.
- The three hybrid plants now check growth every 40–80 ticks (about 2–4 seconds), down from 200–400 ticks (10–20 seconds).
- When two different hybrid species are both mature within about 3 blocks, they persistently cross-pollinate; each pollinated plant gives one extra harvest item, then clears the saved pollination state. This remains gated by the existing Hybrid Plants switch (off by default).
- Pollination discovery scans at most once per plant every 200 game ticks and keeps a 512-entry transient scan cache; the saved pollination state remains on the block.
- Expanded the saved, two-path Field Story from five to ten chapters. Garden and Ruin routes have different later objectives; progress and rewards still save before XP is granted.
- Water, Lava, and Phantom creeper movement switches are now reapplied when those entities load from an unloaded chunk, even if their one-time spawn setup already ran.
- Newly spread microscopic spores now appear after 1–5 seconds by default instead of waiting 5–60 seconds. Saved ranges changed away from the old defaults are preserved; untouched old defaults receive the faster range.
- Toxic-spore contact reactions now include all 18 listed animals/hostile mob types, with the existing villager warning and iron-golem colony response covering the other three named species.
- The 0.8.1 story foundation, all 23 creeper identifiers/artworks, carrier rules, and current systems are retained.

INSTALLATION
Import Creeper_Spores_0.8.30_Expanded.mcaddon with Minecraft closed, then open the imported pack and enable both behavior and resource packs on a disposable world. If Minecraft reports a duplicate, check whether the same version is already installed. Keep active worlds backed up before changing pack versions.

VERIFICATION
- Offline tests check JSON, JavaScript syntax/imports, manifests, resource references, all 23 Creeper assets and distinct pursuit/fuse/roaming profiles, all 64 strain/stage spore textures and growth-hook wiring, recipe outputs, 0.8 systems, ten-chapter story path/completion, 56 spore transitions, movement-switch reload behavior, mob-reaction species coverage and nearby vertical search, colony grouping, dual-phase blast fallback/deduplication, and normal/charged blast seeding.
- All 23 supplied concept images are preserved in the complete package; their PNG contents match the desktop reference files byte-for-byte.
- 0.8.1 PC smoke test evidence is carried forward as historical only: Minecraft accepted the journal item and summoned a custom creeper in a disposable world.
- 0.8.30 has not yet been tested in Minecraft. In particular, the new raised blast seed and its continued growth require a fresh in-game test.

STILL INCOMPLETE OR UNVERIFIED
- Full unique target selection and tactical combat AI for every Creeper variant; all 23 now have tuned alert/fuse/roaming/pursuit ranges, and blast status effects are defined, but actual targeting, balance, and combat still need in-game tests.
- Correct swimming, lava movement, phantom flight, actual wind and water-current physics, rain runoff, and all transfer edge cases.
- Persistent world-spanning synchronized colonies and full colony coordination.
- The complete crop/plant ecology, all biome hybrids, suppression, withering, deeper genetic hybrid breeding, and species-specific animal interactions.
- Vanilla villager profession trades; the existing researcher trader is separate.
- Full authored structures and guaranteed world generation across all requested biomes; scripted micro-ruins now have three layouts, while generation breadth and runtime placement remain limited/unverified.
- Full drawn persistent atlas, in-game dialogue scenes, and a longer authored campaign are still incomplete; 0.8.30 provides a ten-chapter two-path Field Story using existing journal events.
- Larger industrial redstone factories, physical opening pod geometry, full hatch scenes, and final lantern/ornament models. The Spore Controller now supports a bounded, extract-fed auto-seed mode; its in-game behavior still needs testing. The four armor pieces now have in-game attachable definitions, though their equipped appearance is not runtime-verified.
- Reliable protection for old builds and command/add-on placed blocks.
- All Bedrock runtime checks, content logs, all strain growth, explosion timing/drops, optional biome generation, environmental abilities, player pod contact, in-game visual matching against all 23 references, migration, multiplayer, mobile/controller/server, and long-session performance.
- Any previously conflicting exact biome or growth preferences remain unchanged rather than guessed.
