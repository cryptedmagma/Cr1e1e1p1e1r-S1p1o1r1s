// Creeper Spores - entry point. Behaviour is split across modules; see IMPLEMENTATION_STATUS.md.
import { system } from "@minecraft/server";
import { registerBlock, tickPending } from "./spores.js";
import { registerHybridPlants } from "./hybrid_plants.js";
import { registerNewItems } from "./new_items.js";
import { registerItems } from "./items.js";
import "./explosions.js";   // subscribes to creeper-family blasts
import "./players.js";    // carriers, toxic contact, hatchling shedding
import "./entities.js";   // special-movement switches + first-spawn init
import "./diag.js";       // failure diagnostics + /scriptevent cs:diag
import "./ecology.js";    // colony spread, crop + mob ecology
import { registerController } from "./redstone.js";
import { registerExpansionItems, registerExpansionBlocks } from "./expansion_items.js";
import "./colony_networks.js"; // loaded connected-colony graph and gated cooperation
import "./variant_ecology.js"; // environment-appropriate variants, opt-in
import "./placed_block_guard.js"; // conservative player-placement records from 0.8 forward
import "./field_ruins.js"; // designed micro-ruins, opt-in and non-destructive
import "./airborne_clouds.js"; // finite visible travelling clouds
import "./traps.js"; // harvested airborne particles
import "./advanced_spread.js";  // water/rain/wind/vine/leaf and transport carriers
import "./terrain.js";          // reversible infected terrain with saved original blocks
import "./worldgen.js";         // opt-in natural establishment
import "./structure_encounters.js"; // PRE-RELEASE structure API; guarded and opt-in
import "./plant_ecology.js";   // additional vegetation without destructive crop replacement
import "./splash_route.js"; // optional splash-potion route
import "./mob_reactions.js";
import "./test_tools.js"; // explicit /scriptevent in-world regression helpers    // independently gated mob and villager responses   // spore controller block

system.beforeEvents.startup.subscribe(({ blockComponentRegistry, itemComponentRegistry }) => {
  registerBlock(blockComponentRegistry);
  registerHybridPlants(blockComponentRegistry);
  registerItems(itemComponentRegistry);
  registerNewItems(itemComponentRegistry);
  registerController(blockComponentRegistry);
  registerExpansionItems(itemComponentRegistry);
  registerExpansionBlocks(blockComponentRegistry);
});

// Microscopic spores: bounded batch every second (the original scanned every tick).
system.runInterval(tickPending, 20);
