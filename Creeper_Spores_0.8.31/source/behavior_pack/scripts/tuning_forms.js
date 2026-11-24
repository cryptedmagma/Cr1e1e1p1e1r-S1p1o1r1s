import { ModalFormData } from "@minecraft/server-ui";
import { getLocalTuning, setLocalTuning, SUBSTRATES, BIOMES } from "./tuning.js";
import { isAdmin } from "./config.js";
export async function openLocalTuning(player){
 try{
  if(!isAdmin(player))return;
  const before=getLocalTuning();
  const f=new ModalFormData().title("Spore Local Growth & Generation")
    .dropdown("Mechanism",["Substrate growth speed", "Biome natural spore chance"],{defaultValueIndex:0})
    .dropdown("Substrate",SUBSTRATES,{defaultValueIndex:0})
    .dropdown("Biome",BIOMES,{defaultValueIndex:0})
    .slider("Multiplier (1 = neutral, no invented priority)",0,3,{valueStep:0.05,defaultValue:1});
  const r=await f.show(player);if(r.canceled||!r.formValues)return;
  if(!isAdmin(player))return;
  const [kind,s,b,m]=r.formValues;const group=kind===0?"growth":"biome";
  const key=group==='growth'?SUBSTRATES[s]:BIOMES[b];
  const value=Number(m);
  if(value<0.25&&group==='growth')return player.sendMessage("§cSubstrate multipliers must be at least 0.25.");
  if(setLocalTuning(group,key,value,before.revision))player.sendMessage(`§a${group} ${key} multiplier = ${value}. Saved for future updates.`);
  else player.sendMessage("§cSetting could not be saved (or another administrator changed it first).");
 }catch(e){try{player.sendMessage("§cTuning menu error: "+String(e).slice(0,90));}catch{}}
}
