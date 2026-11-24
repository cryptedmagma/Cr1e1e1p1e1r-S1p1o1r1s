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
// 0.8.31: each Spore-Proof piece has its own ability against themed creeper-blast effects.
// The older rules are unchanged: any piece blocks toxic-pod poison on contact, and a full
// four-piece suit cannot carry spores.
export const PIECE_SLOT = Object.freeze({
  Head: "cookiedookie:spore_helmet", Chest: "cookiedookie:spore_chestplate",
  Legs: "cookiedookie:spore_leggings", Feet: "cookiedookie:spore_boots",
});
export const PIECE_BLOCKS = Object.freeze({
  Head: ["blindness", "darkness", "nausea"], // Filter Visor: keeps spore haze out of the eyes
  Chest: ["poison", "hunger"],               // Sealed Weave: no toxic spores reach the lungs
  Legs: ["slowness"],                        // Braced Greaves: legs keep moving through spore sludge
  Feet: ["weakness"],                        // Anchored Treads: footing stays sure after a blast
});
/** Pure rule: does a set of worn piece ids block this effect? */
export function piecesBlockEffect(wornBySlot, effectName) {
  for (const [slot, effects] of Object.entries(PIECE_BLOCKS)) {
    if (wornBySlot[slot] === PIECE_SLOT[slot] && effects.includes(effectName)) return true;
  }
  return false;
}
export function armorBlocksEffect(player, effectName) {
  try {
    const eq = player.getComponent("minecraft:equippable") ?? player.getComponent("equippable");
    if (!eq) return false;
    const worn = {};
    for (const slot of Object.keys(PIECE_SLOT)) worn[slot] = eq.getEquipment(slot)?.typeId;
    return piecesBlockEffect(worn, effectName);
  } catch { return false; }
}
