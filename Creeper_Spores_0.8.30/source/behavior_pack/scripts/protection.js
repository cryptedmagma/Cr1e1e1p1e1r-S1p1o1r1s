// Creeper Spores 0.4.0 — protection is player/equipment-specific, not a world-wide flag.
const ids = new Set(["cookiedookie:spore_helmet", "cookiedookie:spore_chestplate", "cookiedookie:spore_leggings", "cookiedookie:spore_boots"]);
export function protectionPieces(player) {
  try {
    const eq=player.getComponent("minecraft:equippable") ?? player.getComponent("equippable");
    if (!eq) return 0;
    let found=0;
    for(const slot of ["Head","Chest","Legs","Feet"]){
      const stack=eq.getEquipment(slot);
      if(stack&&ids.has(stack.typeId))found++;
    }
    return found;
  } catch{return 0;}
}
export function hasSporeProtection(player) {return protectionPieces(player)>0;}
