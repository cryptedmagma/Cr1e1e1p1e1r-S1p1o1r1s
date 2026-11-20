// Creeper Spores 0.6.0 — 23 variant registry; preserved stable identifiers for original 20.
export const STRAINS = [
  {
    "key": "normal",
    "name": "Common Spore",
    "growth": 1.0,
    "drop": null,
    "light": 0,
    "info": "The original spore. Grows on any firm ground."
  },
  {
    "key": "luminous",
    "name": "Luminous Spore",
    "growth": 0.9,
    "drop": "luminous_shard",
    "light": 7,
    "info": "Glows softly. Appears in deep caves and near glowstone. Hatches glowing creepers."
  },
  {
    "key": "toxic",
    "name": "Toxic Spore",
    "growth": 1.0,
    "drop": null,
    "light": 0,
    "info": "Poisonous to touch once the pod swells. Favours swamps and mud."
  },
  {
    "key": "frost",
    "name": "Frost Spore",
    "growth": 0.6,
    "drop": null,
    "light": 0,
    "info": "Cold-adapted and slow growing. Hatches snow creepers."
  },
  {
    "key": "ember",
    "name": "Ember Spore",
    "growth": 1.0,
    "drop": "volatile_essence",
    "light": 4,
    "info": "Fire resistant. Found in the Nether or beside magma."
  },
  {
    "key": "aqua",
    "name": "Aqua Spore",
    "growth": 1.0,
    "drop": null,
    "light": 0,
    "info": "Water adapted. Hatches water creepers."
  },
  {
    "key": "sculk",
    "name": "Sculk Spore",
    "growth": 0.8,
    "drop": null,
    "light": 0,
    "info": "Sculk-infused. Hatches sculk and phantom creepers."
  },
  {
    "key": "royal",
    "name": "Royal Spore",
    "growth": 0.5,
    "drop": null,
    "light": 3,
    "info": "Made with a Spore Catalyst. Slow, but may hatch a Spore Queen."
  }
];
export const VARIANTS = {
  "moss": {
    "id": "cookiedookie:moss_creeper",
    "name": "Moss Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "cave": {
    "id": "cookiedookie:cave_creeper",
    "name": "Cave Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "darkness",
      "ticks": 60,
      "amp": 0,
      "radius": 4
    }
  },
  "crystal": {
    "id": "cookiedookie:crystal_creeper",
    "name": "Crystal Creeper",
    "strain": 1,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "swamp": {
    "id": "cookiedookie:swamp_creeper",
    "name": "Swamp Creeper",
    "strain": 2,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "poison",
      "ticks": 100,
      "amp": 0,
      "radius": 5
    }
  },
  "desert": {
    "id": "cookiedookie:desert_creeper",
    "name": "Desert Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "hunger",
      "ticks": 200,
      "amp": 0,
      "radius": 5
    }
  },
  "snow": {
    "id": "cookiedookie:snow_creeper",
    "name": "Snow Creeper",
    "strain": 3,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 100,
      "amp": 1,
      "radius": 5
    }
  },
  "jungle": {
    "id": "cookiedookie:jungle_creeper",
    "name": "Jungle Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "poison",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "mushroom": {
    "id": "cookiedookie:mushroom_creeper",
    "name": "Mushroom Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "nausea",
      "ticks": 100,
      "amp": 0,
      "radius": 4
    }
  },
  "sculk": {
    "id": "cookiedookie:sculk_creeper",
    "name": "Sculk Creeper",
    "strain": 6,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "darkness",
      "ticks": 100,
      "amp": 0,
      "radius": 6
    }
  },
  "nether": {
    "id": "cookiedookie:nether_creeper",
    "name": "Nether Creeper",
    "strain": 4,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "weakness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "end": {
    "id": "cookiedookie:end_creeper",
    "name": "End Creeper",
    "strain": 1,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "nausea",
      "ticks": 100,
      "amp": 0,
      "radius": 5
    }
  },
  "water": {
    "id": "cookiedookie:water_creeper",
    "name": "Water Creeper",
    "strain": 5,
    "rmul": 1.0,
    "height": 1.7,
    "move": "water",
    "effect": {
      "name": "weakness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "lava": {
    "id": "cookiedookie:lava_creeper",
    "name": "Lava Creeper",
    "strain": 4,
    "rmul": 1.0,
    "height": 1.7,
    "move": "lava",
    "effect": {
      "name": "slowness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "flower": {
    "id": "cookiedookie:flower_creeper",
    "name": "Flower Creeper",
    "strain": 0,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "regeneration",
      "ticks": 100,
      "amp": 0,
      "radius": 5
    }
  },
  "thorn": {
    "id": "cookiedookie:thorn_creeper",
    "name": "Thorn Creeper",
    "strain": 2,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "weakness",
      "ticks": 100,
      "amp": 0,
      "radius": 4
    }
  },
  "phantom": {
    "id": "cookiedookie:phantom_creeper",
    "name": "Phantom Creeper",
    "strain": 6,
    "rmul": 1.0,
    "height": 1.7,
    "move": "phantom",
    "effect": {
      "name": "blindness",
      "ticks": 60,
      "amp": 0,
      "radius": 5
    }
  },
  "giant": {
    "id": "cookiedookie:giant_creeper",
    "name": "Giant Creeper",
    "strain": 0,
    "rmul": 1.75,
    "height": 3.4,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 100,
      "amp": 0,
      "radius": 6
    }
  },
  "miniature": {
    "id": "cookiedookie:miniature_creeper",
    "name": "Miniature Creeper",
    "strain": 0,
    "rmul": 0.5,
    "height": 0.85,
    "move": null,
    "effect": {
      "name": "weakness",
      "ticks": 60,
      "amp": 0,
      "radius": 3
    }
  },
  "glowing": {
    "id": "cookiedookie:glowing_creeper",
    "name": "Glowing Creeper",
    "strain": 1,
    "rmul": 1.0,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "blindness",
      "ticks": 50,
      "amp": 0,
      "radius": 4
    }
  },
  "spore_queen": {
    "id": "cookiedookie:spore_queen_creeper",
    "name": "Spore Queen",
    "strain": 7,
    "rmul": 2.0,
    "height": 2.2,
    "move": null,
    "effect": {
      "name": "weakness",
      "ticks": 160,
      "amp": 0,
      "radius": 8
    }
  },
  "grass_crown": {
    "id": "cookiedookie:grass_crown_creeper",
    "name": "Grass Crown Creeper",
    "strain": 0,
    "rmul": 1,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 60,
      "amp": 0,
      "radius": 4
    }
  },
  "carved_wood": {
    "id": "cookiedookie:carved_wood_creeper",
    "name": "Carved Wood Creeper",
    "strain": 0,
    "rmul": 1,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "weakness",
      "ticks": 80,
      "amp": 0,
      "radius": 4
    }
  },
  "slender_green": {
    "id": "cookiedookie:slender_green_creeper",
    "name": "Slender Green (Bamboo) Creeper",
    "strain": 0,
    "rmul": 1,
    "height": 1.7,
    "move": null,
    "effect": {
      "name": "slowness",
      "ticks": 60,
      "amp": 0,
      "radius": 4
    }
  }
};
export const SEED_ITEMS = {
  "cookiedookie:seed_luminous": 1,
  "cookiedookie:seed_toxic": 2,
  "cookiedookie:seed_frost": 3,
  "cookiedookie:seed_ember": 4,
  "cookiedookie:seed_aqua": 5,
  "cookiedookie:seed_sculk": 6,
  "cookiedookie:seed_royal": 7
};
