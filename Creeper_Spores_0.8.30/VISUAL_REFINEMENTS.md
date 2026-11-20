# Creeper Spores — reference-based 3D refinements

All 23 custom Bedrock Creeper geometries have been refined using the user-supplied contact sheet. Existing 0.8.30 entity IDs, skins, animation names, behavior logic, scripts, spawn rules and pack UUIDs are preserved.

- Nature designs: hanging moss, jungle canopies, swamp reeds, grass crown, flowers, thorns.
- Mineral and heat designs: cave formations, crystal shards, sandstone/cactus detailing, icy overhangs, Nether and lava projections.
- Fantasy designs: sculk tendrils, end stalks, phantom wing hems, Spore Queen mushrooms and surface nodules.
- Scale designs: separate giant, miniature, carved wood and slender-green silhouettes.
- Fix: offset duplicate foot decorations onto their corresponding animated legs on applicable models.

## One-run packaging from the current checked-out source

Run this command at the repository root:

    python Creeper_Spores_0.8.30/build_from_checkout.py

The script validates all 23 model/client/behavior links, 92 variant skins, texture atlas UV limits and pack UUID dependencies. It then writes Creeper_Spores_0.8.30/dist/Creeper_Spores_Visual_Refined.mcaddon and individual .mcpack files (plus optional worldgen if present). No installation, prompts or internet requests required.

Do not build from the preexisting Source_And_Offline_Tests.zip or import the preexisting Expanded.mcaddon from main: those archives are prior exports and do not contain these new geometry changes.

## Acceptance / limits

The supplied images are rendered concepts; exact visual parity, bloom, lighting, translucency and movement remain **unverified** until tested in Minecraft Bedrock. Use a disposable world and inspect each mob front, side and back under day and night lighting, including charged skins and leg movement. Existing pack manifests specify Bedrock min_engine_version 1.21.130. Test summon with:

    /summon cookiedookie:spore_queen_creeper ~ ~ ~

No current release .mcaddon is asserted to be in-game tested.
