"""0.8.31 source regression checks. Offline and schema-level only, not Bedrock execution."""
from pathlib import Path
import hashlib
import subprocess,json,zipfile,re,sys,tempfile
BASE=Path(__file__).parent;BP=BASE/'behavior_pack';RP=BASE/'resource_pack';SRC=BP/'scripts'
check=0

def ok(test,msg):
 global check
 assert test,msg
 check+=1

for p in BASE.rglob('*.json'):
 json.loads(p.read_text());check+=1
for p in SRC.glob('*.js'):
 v=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 ok(v.returncode==0,f'{p.name}: {v.stderr}')
 for dep in re.findall(r'(?:from|import)\s+["\'](\./[^"\']+)["\']',p.read_text()):
  ok((p.parent/dep).is_file(),f'missing JS import {p.name}: {dep}')
for kind in ['behavior_pack','resource_pack']:
 m=json.loads((BASE/kind/'manifest.json').read_text())
 ok(m['header']['version']==[0,8,31],f'{kind} version')
 for dep in m.get('dependencies',[]):
  if dep.get('uuid'):ok(dep['version']==[0,8,31],f'{kind} dependency version')
optional_manifest=json.loads((BASE/'optional_worldgen_pack'/'manifest.json').read_text())
ok(optional_manifest['header']['version']==[0,8,31],'optional worldgen pack version')
ok(optional_manifest['dependencies'][0]['version']==[0,8,31],'optional worldgen dependency version')
tex_t=json.loads((RP/'textures/terrain_texture.json').read_text())['texture_data']
tex_i=json.loads((RP/'textures/item_texture.json').read_text())['texture_data']
for d in [tex_t,tex_i]:
 for k,v in d.items():
  x=v['textures']
  for ref in x if isinstance(x,list) else [x]:
   if isinstance(ref,str):ok((RP/(ref+'.png')).is_file(),f'missing texture: {k}: {ref}')
entity_names=['moss','cave','crystal','swamp','desert','snow','jungle','mushroom','sculk','nether','end','water','lava','flower','thorn','phantom','giant','miniature','glowing','spore_queen','grass_crown','carved_wood','slender_green']
for key in entity_names:
 ok((BP/f'entities/{key}_creeper.json').is_file(),f'entity missing {key}')
 ok((RP/f'models/entity/{key}_creeper.geo.json').is_file(),f'geometry missing {key}')
 ok((RP/f'textures/entity/cookiedookie/{key}_creeper.png').is_file(),f'texture missing {key}')
# 0.8.31 rebuilt every creeper model: per-cube, per-face UV regions on a painted atlas, matched to the concept art.
import struct
def png_size(path):
 raw=path.read_bytes();ok(raw[:8]==bytes.fromhex('89504e470d0a1a0a'),f'not a PNG: {path.name}')
 return struct.unpack('>II',raw[16:24])
for key in entity_names:
 model=json.loads((RP/f'models/entity/{key}_creeper.geo.json').read_text())
 ok(model['format_version']=='1.12.0',f'{key}: geometry format must support cube rotations')
 geo=model['minecraft:geometry'][0];desc=geo['description']
 ok(desc['identifier']==f'geometry.cookiedookie.{key}_creeper',f'{key}: geometry identifier')
 bones={b['name']:b for b in geo['bones']}
 for need in ('body','head','leg0','leg1','leg2','leg3'):ok(need in bones,f'{key}: rig bone {need} needed by creeper leg/ambient animations')
 ok(bones['head'].get('parent')=='body',f'{key}: head must follow the body')
 for b in geo['bones']:
  if 'parent' in b:ok(b['parent'] in bones,f'{key}: bone {b["name"]} has unknown parent')
 tw,th=desc['texture_width'],desc['texture_height']
 for variant in ('','_alt','_charged','_alt_charged'):
  ok(png_size(RP/f'textures/entity/cookiedookie/{key}_creeper{variant}.png')==(tw,th),f'{key}{variant}: texture size must match geometry ({tw}x{th})')
 cubes=[c for b in geo['bones'] for c in b.get('cubes',[])]
 ok(len(cubes)>=6,f'{key}: model lost its body parts')
 regions=[]
 for c in cubes:
  ok(isinstance(c.get('uv'),dict) and c['uv'],f'{key}: cube without per-face UV')
  if 'rotation' in c:ok(len(c['rotation'])==3 and len(c.get('pivot',[]))==3,f'{key}: rotated cube needs a pivot')
  for face,f in c['uv'].items():
   u,v=f['uv'];w,h=f['uv_size']
   ok(0<=u and 0<=v and u+w<=tw and v+h<=th and w>0 and h>0,f'{key}: {face} UV outside the {tw}x{th} atlas')
   regions.append((u,v,w,h))
 ok(len(set(regions))==len(regions),f'{key}: two faces share one UV region (atlas must give each face its own pixels)')
 head_cube=bones['head']['cubes'][0]
 ok('north' in head_cube['uv'],f'{key}: head front face (creeper face) missing')
# Glowing variants: emissive pixels (0 < alpha < 255; alpha 0 is unused atlas space) are only safe under Bedrock's entity_emissive_alpha material.
from PIL import Image as _Img
glowing=set()
for key in entity_names:
 mat=json.loads((RP/f'entity/{key}_creeper.entity.json').read_text())['minecraft:client_entity']['description']['materials']['default']
 a=[_Img.open(RP/f'textures/entity/cookiedookie/{key}_creeper{v}.png').getchannel('A') for v in ('','_alt','_charged','_alt_charged')]
 has=any(sum(ch.histogram()[1:255])>0 for ch in a)
 ok(mat==('entity_emissive_alpha' if has else 'creeper'),f'{key}: material {mat} does not match its texture alpha')
 if has:glowing.add(key)
ok({'lava','sculk','glowing','nether','end'}<=glowing,'core glowing variants must carry emissive pixels')
# Signature details from the concept art.
crystal=json.loads((RP/'models/entity/crystal_creeper.geo.json').read_text())['minecraft:geometry'][0]
cb={b['name']:b for b in crystal['bones']}
ok(sum(1 for n,bb in cb.items() if n=='head' or bb.get('parent')=='head' for c in bb.get('cubes',[]) if 'rotation' in c)>=10,'crystal crown needs its leaning shard cluster')
ok(all(any('rotation' in c for c in cb[f'leg{i}']['cubes']) for i in range(4)),'crystal: every foot needs a crystal')
phantom=json.loads((RP/'models/entity/phantom_creeper.geo.json').read_text())['minecraft:geometry'][0]
pbody=next(b for b in phantom['bones'] if b['name']=='body')
left=[c for c in pbody['cubes'] if 'rotation' in c and c['origin'][0]>=0];right=[c for c in pbody['cubes'] if 'rotation' in c and c['origin'][0]<0]
ok(len(left)>=10 and len(left)==len(right),'phantom: ragged wings must be mirrored left/right')
ok(sorted(c['rotation'][2] for c in left)==sorted(-c['rotation'][2] for c in right),'phantom: wing angles must mirror')
ok(sum(1 for b in json.loads((RP/'models/entity/jungle_creeper.geo.json').read_text())['minecraft:geometry'][0]['bones'] if b['name'].startswith(('head_frond','canopy_leaf')))>=8,'jungle: palm-frond crown missing')
# Blast deposits begin at the visibly larger age-3 model without changing their true growth state.
blast_geo=json.loads((RP/'models/blocks/creeper_spores.age_3.geo.json').read_text())['minecraft:geometry'][0]
ok(any(c.get('size')==[5,8,5] for b in blast_geo['bones'] for c in b.get('cubes',[])),'blast starting stage lacks the larger age-3 model')
# Variant-specific pursuit, fuse trigger, and roaming values make the base AI differ per Creeper.
ai_profiles=[]
for key in entity_names:
 e=json.loads((BP/f'entities/{key}_creeper.json').read_text())['minecraft:entity']
 c=e['components'];swell=c['minecraft:behavior.swell'];sensor=c['minecraft:target_nearby_sensor'];target=c['minecraft:behavior.nearest_attackable_target'];roam=c['minecraft:behavior.random_stroll'];melee=c['minecraft:behavior.melee_attack']
 alert=target['within_radius'];start=swell['start_distance'];stop=swell['stop_distance'];speed=roam['speed_multiplier'];chase=melee['speed_multiplier']
 ok(target['entity_types'][0]['max_dist']==alert,f'{key}: target range disagrees with selection radius')
 ok(sensor['inside_range']==start and sensor['outside_range']==stop,f'{key}: swell sensor disagrees with fuse distances')
 ok(1.5<=start<=4.5 and stop>=start+1 and 10<=alert<=26 and 0.6<=speed<=1.25,f'{key}: AI profile outside validated tuning range')
 ok(0.75<=chase<=1.5 and chase==round(min(1.5,max(.75,speed*1.25)),2),f'{key}: chase speed does not follow the tuned roaming profile')
 ai_profiles.append((alert,start,stop,speed,chase))
ok(len(set(ai_profiles))==23,'Creeper variants must have individually tuned pursuit/fuse/roaming profiles')
# Preserve and map each user reference image to its creeper entity/model/texture.
reference_dir=BASE/'reference_art';reference=json.loads((reference_dir/'manifest.json').read_text())
ok(len(reference)==23,'all 23 reference images must be present')
ok(len(list(reference_dir.glob('*.png')))==23,'reference image count changed')
for name,row in reference.items():
 img=reference_dir/name
 ok(img.is_file(),f'reference art missing: {name}')
 ok(hashlib.sha256(img.read_bytes()).hexdigest()==row['sha256'],f'reference image changed: {name}')
 key=row['entity_key']
 ok(key in entity_names,f'reference mapped to unknown creeper: {name}: {key}')
 client=json.loads((RP/row['entity_json']).read_text())['minecraft:client_entity']['description']
 ok(client['geometry']['default']==f'geometry.cookiedookie.{key}_creeper',f'reference geometry mapping mismatch: {name}')
 ok(client['textures']['default']==row['texture'].removesuffix('.png'),f'reference texture mapping mismatch: {name}')
# Four wearable items now bind to Bedrock player armor geometry and dedicated UV-aligned textures.
armor={
 'spore_helmet':('slot.armor.head','geometry.player.armor.helmet','spore_1','helmet_layer_visible'),
 'spore_chestplate':('slot.armor.chest','geometry.player.armor.chestplate','spore_1','chest_layer_visible'),
 'spore_leggings':('slot.armor.legs','geometry.player.armor.leggings','spore_2','leg_layer_visible'),
 'spore_boots':('slot.armor.feet','geometry.player.armor.boots','spore_1','boot_layer_visible'),
}
attach_dir=RP/'attachables';ok(len(list(attach_dir.glob('spore_*.player.json')))==4,'all four armor attachables must exist')
for key,(slot,geometry,texture,layer) in armor.items():
 a=json.loads((attach_dir/f'{key}.player.json').read_text())['minecraft:attachable']['description']
 item=json.loads((BP/f'items/{key}.json').read_text())['minecraft:item']
 ok(a['identifier']==f'cookiedookie:{key}.player',f'{key}: attachable identifier')
 ok(f'cookiedookie:{key}' in a['item'],f'{key}: attachable is not bound to the item')
 ok(item['components']['minecraft:wearable']['slot']==slot,f'{key}: wearable slot')
 ok(a['geometry']['default']==geometry and a['scripts']['parent_setup']==f'variable.{layer} = 0.0;',f'{key}: player armor model/layer mapping')
 tex=a['textures']['default'];png=RP/(tex+'.png');raw=png.read_bytes()
 ok(png.is_file() and raw[:8]==b'\x89PNG\r\n\x1a\n' and int.from_bytes(raw[16:20],'big')==64 and int.from_bytes(raw[20:24],'big')==32,f'{key}: armor layer texture missing or not 64x32')
 ok(a['materials']['default']=='armor' and a['materials']['enchanted']=='armor_enchanted' and 'controller.render.armor' in a['render_controllers'],f'{key}: armor render configuration')
# Controller mode 4 is a schema-backed powered auto-seeder with an existing texture resource.
controller=json.loads((BP/'blocks/spore_controller.json').read_text())['minecraft:block']
ok(controller['description']['states']['cookiedookie:mode']['values']['max']==4,'controller must expose fifth Auto Seed mode')
ok(any(p.get('condition')=="query.block_state('cookiedookie:mode') == 4" and p.get('components',{}).get('minecraft:material_instances',{}).get('*',{}).get('texture')=='cookiedookie:spore_controller.m4' for p in controller['permutations']),'Auto Seed mode render mapping')
ok('cookiedookie:spore_controller.m4' in tex_t and (RP/(tex_t['cookiedookie:spore_controller.m4']['textures']+'.png')).is_file(),'Auto Seed mode texture resource')
redstone_source=(SRC/'redstone.js').read_text()
ok('"Auto Seed"' in redstone_source and '% MODE_NAMES.length' in redstone_source and 'else if(mode===4)' in redstone_source,'redstone controller cycles and dispatches Auto Seed')
# All eight strain states and all eight visible ages must have a real texture and ticking growth hook.
spore_block=json.loads((BP/'blocks/creeper_spores.json').read_text())['minecraft:block']
age_state=spore_block['description']['states']['cookiedookie:age']['values']
strain_state=spore_block['description']['states']['cookiedookie:strain']['values']
ok(age_state=={'min':0,'max':7},'spore stages must remain 0..7')
ok(strain_state=={'min':0,'max':7},'spore strains must remain 0..7')
ok(spore_block['components'].get('minecraft:tick',{}).get('looping') is True,'spore growth ticks must loop')
tick_range=spore_block['components'].get('minecraft:tick',{}).get('interval_range',[])
ok(tick_range==[20,40],'all spore strains must receive a growth callback every 1–2 seconds')
ok('cookiedookie:creeper_spores' in spore_block['components'],'spore growth component absent from block')
spores_js=(SRC/'spores.js').read_text()
ok('registry.registerCustomComponent(`${NS}:creeper_spores`' in spores_js and 'onTick({ block })' in spores_js,'spore block tick handler missing')
entities_js=(SRC/'entities.js').read_text()
ok('world.afterEvents.entityLoad?.subscribe' in entities_js,'special movement is not reapplied when creepers reload from chunks')
ok('if (entity && MOVERS[entity.typeId]) applyMovement(entity)' in entities_js,'load handler does not refresh special movement switches')
config_js=(SRC/'config.js').read_text()
ok('germinationMinTicks: 20' in config_js and 'germinationMaxTicks: 100' in config_js,'microscopic spores retain a long visibility delay')
ok('cfg.germinationMinTicks === 100 && cfg.germinationMaxTicks === 1200' in config_js,'old default germination delay is not migrated')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_config.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const original=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n').replace(/^import .*;\s*$/gm,'').replace(/\bexport\s+(const|function)\b/g,'$1');
function load(saved){let stored=JSON.stringify(saved);const world={getDynamicProperty:()=>stored,setDynamicProperty:(_k,v)=>stored=v};
 const ctx={world};vm.runInNewContext(original+';globalThis.readConfig=getConfig;',ctx);const config=ctx.readConfig();return {config,stored:JSON.parse(stored)};}
const old=load({germinationMinTicks:100,germinationMaxTicks:1200});
assert.equal(old.config.germinationMinTicks,20);assert.equal(old.config.germinationMaxTicks,100);
assert.equal(old.stored.germinationMinTicks,20);assert.equal(old.stored.germinationMaxTicks,100,'migration must persist');
const chosen=load({germinationMinTicks:100,germinationMaxTicks:600});
assert.equal(chosen.config.germinationMinTicks,100);assert.equal(chosen.config.germinationMaxTicks,600,'custom delay should remain');
console.log('Germination config: legacy defaults migrate; custom timing preserved');''')
 r=subprocess.run(['node',str(q/'test_config.cjs'),str(SRC/'config.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Toxin-contact reaction profiles cover every named mob species in the accepted ecology list.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_reactions.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=source.indexOf('const effects = {'),end=source.indexOf('};\nlet index',start);
assert(start>=0&&end>start,'mob reaction table not found');
assert(source.includes('for(const dy of [-1,0,1,2])'),'mob reaction scan ignores nearby flying/swimming species');
const context={};vm.runInNewContext(source.slice(start,end+1)+';globalThis.effects=effects;',context);
const required=['minecraft:cow','minecraft:sheep','minecraft:pig','minecraft:chicken','minecraft:rabbit','minecraft:wolf','minecraft:cat','minecraft:fox','minecraft:bee','minecraft:zombie','minecraft:skeleton','minecraft:spider','minecraft:enderman','minecraft:witch','minecraft:slime','minecraft:frog','minecraft:allay','minecraft:warden'];
for(const id of required)assert.ok(context.effects[id],`missing toxin response for ${id}`);
for(const id of ['minecraft:villager','minecraft:villager_v2','minecraft:iron_golem'])assert.ok(source.includes(id),`missing special colony response for ${id}`);
console.log(`Mob ecology: ${required.length+3} requested species have a defined local reaction`);''')
 r=subprocess.run(['node',str(q/'test_reactions.cjs'),str(SRC/'mob_reactions.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
for strain in range(8):
 for age in range(8):
  rel=(f'textures/blocks/creeper_spores/creeper_spores_age_{age}.png' if strain==0 else
       f'textures/blocks/creeper_spores/strain_{strain}/age_{age}.png')
  ok((RP/rel).is_file(),f'missing spore visual for strain {strain}, stage {age}: {rel}')
  texture_key=('cookiedookie:creeper_spores.age_%d'%age if strain==0 else
               'cookiedookie:creeper_spores.s%d.age_%d'%(strain,age))
  condition=(f"query.block_state('cookiedookie:age') == {age}" if strain==0 else
             f"query.block_state('cookiedookie:strain') == {strain} && query.block_state('cookiedookie:age') == {age}")
  match=[p for p in spore_block['permutations'] if p.get('condition')==condition]
  ok(len(match)==1,f'spore strain {strain}, stage {age} must have exactly one render mapping')
  material=match[0].get('components',{}).get('minecraft:material_instances',{}).get('*',{})
  ok(material.get('texture')==texture_key,f'spore strain {strain}, stage {age} maps to wrong texture')
  texture_path=json.loads((RP/'textures/terrain_texture.json').read_text())['texture_data'].get(texture_key,{}).get('textures')
  ok(texture_path==rel.removesuffix('.png'),f'spore texture key {texture_key} resolves to wrong PNG')
# Baselines: the bundled 0.7.0 and 0.8.30 archives must be byte-exact, no 0.7.0 file may have been
# deleted, and the 23 reference artworks must equal the original 0.6.1 artwork set.
import io
base_dir=BASE/'baselines'
expected=json.loads((base_dir/'baselines.sha256.json').read_text())
for rel,digest in expected.items():
 ok((BASE/rel).is_file() and hashlib.sha256((BASE/rel).read_bytes()).hexdigest()==digest,f'baseline archive altered or missing: {rel}')
with zipfile.ZipFile(base_dir/'Creeper_Spores_0.7.0_COMPLETE_EVERYTHING.zip') as outer:
 with zipfile.ZipFile(io.BytesIO(outer.read('01_INSTALL/Creeper_Spores_0.7.0_Air_And_Items.mcaddon'))) as z07:
  for n in z07.namelist():
   if not n.endswith('/'):ok((BASE/n).is_file(),f'0.7.0 file removed from the project: {n}')
 with zipfile.ZipFile(io.BytesIO(outer.read('05_ORIGINAL_23_REFERENCE_ART/Creeper_Spores_0.6.1_Exact_23_Original_Artworks.zip'))) as art:
  originals={hashlib.sha256(art.read(n)).hexdigest() for n in art.namelist() if n.endswith('.png')}
ok(len(originals)==23 and originals=={hashlib.sha256(x.read_bytes()).hexdigest() for x in (BASE/'reference_art').glob('*.png')},'reference art differs from the original 23 artworks')
# Custom block custom-component registration must refer to available components.
main=(SRC/'main.js').read_text()
ok('registerHybridPlants(blockComponentRegistry)' in main,'hybrid registries missing')
for name in ['spore_bluebell','spore_bracken','spore_bogcap']:
 doc=json.loads((BP/f'blocks/{name}.json').read_text())['minecraft:block']
 ok(f'cookiedookie:{name}' in doc['components'],f'hybrid custom-component missing {name}')
 ok(doc['components'].get('minecraft:tick',{}).get('interval_range')==[40,80],f'hybrid growth timer too slow {name}')
 ok(doc['description']['states'].get('cookiedookie:pollinated')==[False,True],f'hybrid pollination state missing {name}')
 ok(len(doc['permutations'])==4,f'hybrid ages missing {name}')
 for n in range(4):ok((RP/f'models/blocks/{name}.age_{n}.geo.json').is_file(),f'hybrid geometry {name} {n}')
hybrid_source=(SRC/'hybrid_plants.js').read_text(encoding='utf-8')
ok('export function hasMatureCrossPollinator' in hybrid_source and 'withState(STATE_POLLINATED,true)' in hybrid_source,'mature unlike hybrids do not persist pollination')
ok('crossPollinated?1:0' in hybrid_source and 'withState(STATE_POLLINATED,false)' in hybrid_source,'pollinated harvest bonus or one-time reset missing')
ok('POLLINATION_RECHECK_TICKS=200' in hybrid_source and 'POLLINATION_CACHE_LIMIT=512' in hybrid_source,'hybrid pollination scan is not bounded/throttled')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_pollination.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=src.indexOf('export function hasMatureCrossPollinator('),end=src.indexOf('\nfunction plantOne(',start);
assert(start>=0&&end>start,'cross-pollination scanner missing');
const env={NS:'cookiedookie',STATE_AGE:'age',defs:{spore_bluebell:{},spore_bracken:{},spore_bogcap:{}},HYBRID_BY_ID:new Map(['spore_bluebell','spore_bracken','spore_bogcap'].map(n=>[`cookiedookie:${n}`,n])),getBlockSafe:(d,p)=>d.blocks.get(`${p.x},${p.y},${p.z}`)};
vm.runInNewContext(src.slice(start,end).replace('export function','function ')+';globalThis.pair=hasMatureCrossPollinator;',env);
function scenario(type,age){const d={blocks:new Map()};d.blocks.set('2,64,0',{typeId:`cookiedookie:${type}`,permutation:{getState:()=>age}});return env.pair({dimension:d,x:0,y:64,z:0},'spore_bluebell');}
assert.equal(scenario('spore_bracken',3),true,'different mature hybrids should cross-pollinate');
assert.equal(scenario('spore_bluebell',3),false,'same-species plants should not cross-pollinate');
assert.equal(scenario('spore_bogcap',2),false,'an immature hybrid should not pollinate');
assert.equal(scenario('missing',3),false,'non-hybrid blocks should not pollinate');
console.log('Hybrid pollination: different mature species pair; same/immature/non-hybrids rejected');''')
 r=subprocess.run(['node',str(q/'test_pollination.cjs'),str(SRC/'hybrid_plants.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_pollination_cache.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=src.indexOf('function shouldScanForPollinator('),end=src.indexOf('\n/** A mature hybrid',start);
assert(start>=0&&end>start,'bounded pollination scan helper missing');
const env={LAST:new Map(),POLLINATION_RECHECK_TICKS:200,POLLINATION_CACHE_LIMIT:512};vm.runInNewContext(src.slice(start,end)+';globalThis.due=shouldScanForPollinator;',env);
assert.equal(env.due('one',100),true);assert.equal(env.due('one',299),false);assert.equal(env.due('one',300),true);
for(let i=0;i<513;i++)env.due(`p${i}`,1000);assert.equal(env.LAST.size,512,'pollination cache must remain bounded');
console.log('Pollination scan: one check per 200 ticks and cache capped at 512 plants');''')
 r=subprocess.run(['node',str(q/'test_pollination_cache.cjs'),str(SRC/'hybrid_plants.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
for name in ['luminescent_berry','fungal_fiber','marsh_cap']:
 ok((BP/f'items/{name}.json').exists(),f'harvest item {name}')
 ok((BP/f'recipes/hybrid_{name}.json').exists(),f'harvest recipe {name}')
# Every custom recipe output points to a defined item/block.
ids=set()
for sub,tag in [('items','minecraft:item'),('blocks','minecraft:block'),('entities','minecraft:entity')]:
 for p in (BP/sub).glob('*.json'):
  d=json.loads(p.read_text()).get(tag,{});i=d.get('description',{}).get('identifier')
  if i:ids.add(i)
for p in (BP/'recipes').glob('*.json'):
 d=json.loads(p.read_text());r=next((v for k,v in d.items() if k.startswith('minecraft:recipe')),None)
 if not r:continue
 out=r.get('result',[]);out=out if isinstance(out,list) else [out]
 for o in out:
  i=o.get('item','')
  if i.startswith('cookiedookie:'):ok(i in ids,f'unknown recipe output {p.name}: {i}')
# API guard and design switches
cfg=(SRC/'config.js').read_text();ui=(SRC/'journal.js').read_text()
players=(SRC/'players.js').read_text();ok('playerContactSpore(dim, p.location)' in players,'player contact check is not wired into carrier scanning')
for key in ['colonyNetworks','networkCooperation','variantEcology','hybridPlants','fieldRuins']:
 ok(key in cfg and key in ui,f'{key}: config/ui absent')
for key in ['networkCooperation: false','variantEcology: false','hybridPlants: false','fieldRuins: false']:
 ok(key in cfg,f'{key}: must default OFF')
for name in ['colony_networks','variant_ecology','hybrid_plants','field_ruins','placed_block_guard']:
 ok((SRC/(name+'.js')).exists(),f'missing module {name}')
# Branching field story remains player-private, saved, and reward-safe.
journal=(SRC/'journal.js').read_text()
ok('storyStep' in journal and 'storyPath' in journal,'field story state is not persisted')
ok('Garden Path' in journal and 'Ruin Path' in journal,'both story branches are present')
ok('Math.min(10, j.storyStep | 0)' in journal,'extended story completion state is clamped too early')
for chapter in ['Field Notes in Bloom','The Unfamiliar Face','A Path Through the Roots','Beyond the Familiar World','Keeper of the Record']:
 ok(chapter in journal,f'field story chapter missing: {chapter}')
ok('j.hybridHarvests >= 20' in journal and 'j.nests >= 3' in journal,'late story objectives lost path-specific progression')
ok('j.strains.length >= STRAINS.length && j.variants.length >= 10 && j.scans >= 10' in journal,'final research chapter does not test full record goals')
chapter_save=journal.index('Chapter progress could not be saved')
ok(chapter_save < journal.index('player.addExperience(ch.xp)'),'chapter reward is granted only after progress saves')
ok('f.button("Field Story")' in journal,'field story is absent from the research journal')
# Exercise both story routes and the persisted terminal step in a plain Node VM.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_story.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),env={STRAINS:Array.from({length:8},()=>({}))};
const ns=source.indexOf('function normalize(j) {'),ne=source.indexOf('export function getJournal');assert(ns>=0&&ne>ns);
vm.runInNewContext(source.slice(ns,ne)+';globalThis.normal=normalize;',env);
const ss=source.indexOf('const STORY_CHAPTERS = ['),se=source.indexOf('];\n\nasync function openStory',ss);assert(ss>=0&&se>ss);
vm.runInNewContext(source.slice(ss,se+2)+';globalThis.chapters=STORY_CHAPTERS;',env);
assert.equal(env.normal({storyStep:10}).storyStep,10,'completed story state must survive save/load');
assert.equal(env.chapters.length,10);
const late=env.chapters[7];
assert.equal(late.ready({storyPath:'garden',hybridHarvests:20}),true);
assert.equal(late.ready({storyPath:'garden',hybridHarvests:19}),false);
assert.equal(late.ready({storyPath:'ruins',nests:3,networkFinds:1}),true);
assert.equal(late.ready({storyPath:'ruins',nests:3,networkFinds:0}),false);
assert.equal(env.chapters[9].ready({strains:Array(8),variants:Array(10),scans:10}),true);
console.log('Field Story: 7 mocked progress and completion checks passed');''')
 r=subprocess.run(['node',str(q/'test_story.cjs'),str(SRC/'journal.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Pure function runtime check in Node vm, not Bedrock engine.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_graph.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const folder=process.argv[2];
const env={Math,Set,Map,console,world:{getPlayers:()=>[]},system:{runInterval:()=>{},currentTick:0},getConfig:()=>({}),knownPods:()=>[],getBlockSafe:()=>null,isSpore:()=>false,diag:()=>{}};
let source=fs.readFileSync(folder+'/colony_networks.js','utf8').replace(/^import .*;\s*$/gm,'').replace(/\bexport (const|function|async function)\b/g,'$1');
vm.runInNewContext(source+'\nglobalThis.clusters=colonyClusters;',env);
let N=[{x:0,y:0,z:0},{x:6,y:0,z:0},{x:12,y:0,z:0},{x:50,y:0,z:0}];
let clusters=env.clusters(N);assert.equal(clusters.length,2);assert.equal(clusters[0].size,3);assert.equal(clusters[1].size,1);
assert.equal(env.clusters([]).length,0);
assert.equal(env.clusters([{x:1,y:0,z:0},{x:1,y:0,z:0}]).length,1);
let max=Array.from({length:150},(_,x)=>({x:100*x,y:0,z:0}));assert.equal(env.clusters(max).length,72);
console.log('Colony graph: 5 mocked assertions passed');''')
 r=subprocess.run(['node',str(q/'test_graph.cjs'),str(SRC)],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Exercise the actual stage-advance function with isolated Minecraft block stubs.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_growth.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=src.indexOf('function sporeTick('),end=src.indexOf('function isPeaceful(');
assert(start>=0&&end>start,'spore growth function boundaries not found');
const growth=src.slice(start,end),STATE_AGE='cookiedookie:age',STATE_STRAIN='cookiedookie:strain';
const math=Object.create(Math);math.random=()=>0.99;
const env={Math:math,STATE_AGE,STATE_STRAIN,MAX_AGE:7,STRAINS:Array.from({length:8},()=>({growth:1})),
 getConfig:()=>({growthAdvanceChance:1,mutationChance:0,mutationOutcomes:126}),substrateMultiplier:()=>1,
 getBlockSafe:()=>null,belowOf:b=>({isSolid:true}),aboveOf:()=>null,hasSupport:b=>!!b?.isSolid,isFree:()=>true,
 podHooks:[],noteKnown:()=>{},system:{runTimeout:()=>{}},sound:()=>{},pickMutation:()=>-1,diag:()=>{}};
vm.runInNewContext(growth+';globalThis.advance=sporeTick;',env);
for(let strain=0;strain<8;strain++)for(let age=0;age<7;age++){
 const states={[STATE_AGE]:age,[STATE_STRAIN]:strain,'cookiedookie:rotation':0};
 const perm={getState:k=>states[k],withState:(k,v)=>({getState:q=>q===k?v:states[q],withState:(a,b)=>{const c={...states,[k]:v};c[a]=b;return makePerm(c);}})};
 function makePerm(s){return {getState:k=>s[k],withState:(k,v)=>makePerm({...s,[k]:v})};}
 const block={x:0,y:10,z:0,location:{x:0,y:10,z:0},dimension:{id:'minecraft:overworld'},permutation:perm,setPermutation(p){this.permutation=p;}};
 env.advance(block);
 assert.equal(block.permutation.getState(STATE_AGE),age+1,`strain ${strain} stage ${age} did not advance`);
 assert.equal(block.permutation.getState(STATE_STRAIN),strain,`strain ${strain} changed while growing`);
}
console.log('Spore growth: 56 mocked strain/stage transitions passed');''')
 r=subprocess.run(['node',str(q/'test_growth.cjs'),str(SRC/'spores.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Exercise the real germination writer: incidental deposits remain age 0, while blast callers can choose a bounded visible age.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_germinate.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=src.indexOf('export function germinate('),end=src.indexOf('\n}\n',start)+3;
assert(start>=0&&end>start,'germinate implementation not found');
const states=[],env={SPORE_BLOCK:'cookiedookie:creeper_spores',STATE_ROT:'rotation',STATE_AGE:'age',STATE_STRAIN:'strain',MAX_AGE:7,randRot:()=> '90',sound:()=>{},BlockPermutation:{resolve:(id,s)=>({id,s})}};
vm.runInNewContext(src.slice(start,end).replace('export function','function')+';globalThis.plant=germinate;',env);
function place(...args){const block={dimension:{},location:{},setPermutation(p){this.value=p;}};env.plant(block,...args);return block.value;}
assert.equal(place(0).s.age,0,'ordinary spore germination must remain stage 0');
assert.equal(place(4,2).s.age,2,'blast seeds should begin at visible stage 2');
assert.equal(place(5,4).s.strain,5,'starting stage must preserve strain');
assert.equal(place(3,99).s.age,7,'starting stage must clamp to the final stage');
console.log('Germination writer: default age 0; blast age 2; strain preserved; age bounded');''')
 r=subprocess.run(['node',str(q/'test_germinate.cjs'),str(SRC/'spores.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Mock the Auto Seed controller transaction: a mature colony queues one matching strain and consumes exactly one adjacent extract.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_auto_seed.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n'),start=src.indexOf('function adjacentContainer('),end=src.indexOf('\nfunction act(',start);
assert(start>=0&&end>start,'auto-seed helper boundaries not found');
function scenario({extract=true,mature=true,barrier=false}){
 let item=extract?{typeId:'cookiedookie:spore_extract',amount:2}:undefined;const queued=[],diagnostics=[];
 const container={size:1,getItem:()=>item,setItem:(_i,v)=>{item=v;}};
 const pod={x:1,y:0,z:0,location:{x:1,y:0,z:0},permutation:{getState:k=>k==='cookiedookie:strain'?4:5}};
 const dim={id:'minecraft:overworld'},block={x:0,y:0,z:0,dimension:dim};
 class Stack{constructor(typeId,amount){this.typeId=typeId;this.amount=amount;}}
 const env={NS:'cookiedookie',R:3,ItemStack:Stack,getBlockSafe:(_d,p)=>({typeId:p.y<0?'minecraft:grass_block':'minecraft:air',isAir:p.y>=0,isSolid:p.y<0,location:{...p},getComponent:()=>p.x===1&&p.y===0&&p.z===0?{container}:undefined}),
   isFree:b=>b?.isAir,hasSupport:b=>b?.isSolid,belowOf:b=>({isSolid:true}),blockedBetween:()=>barrier,inZone:()=>false,
   getConfig:()=>({barriersEnabled:true}),addPending:(d,p,s)=>{queued.push({d,p,s});return true;},clearPendingNear:()=>{},
   diag:(...v)=>diagnostics.push(v),scan:()=>mature?[pod]:[],
 };
 vm.runInNewContext(src.slice(start,end)+';globalThis.run=autoSeed;',env);
 return {ok:env.run(block),queued,item,diagnostics};
}
const success=scenario({});assert.equal(success.ok,true);assert.equal(success.queued.length,1);assert.equal(success.queued[0].s,4);assert.equal(success.item.amount,1);
const noExtract=scenario({extract:false});assert.equal(noExtract.ok,false);assert.equal(noExtract.queued.length,0);
const blocked=scenario({barrier:true});assert.equal(blocked.ok,false);assert.equal(blocked.queued.length,0);assert.equal(blocked.item.amount,2);
const noPod=scenario({mature:false});assert.equal(noPod.ok,false);assert.equal(noPod.queued.length,0);assert.equal(noPod.item.amount,2);
console.log('Auto Seed: strain retained, one extract consumed, no mutation through barriers or without a mature pod/input');''')
 r=subprocess.run(['node',str(q/'test_auto_seed.cjs'),str(SRC/'redstone.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Ensure special movement toggles are refreshed after chunk/entity reloads.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_movement.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const saved={},world={afterEvents:{entitySpawn:{subscribe:f=>saved.onSpawn=f},entityLoad:{subscribe:f=>saved.onLoad=f}}};
const cfg={waterMovement:true,lavaMovement:false,phantomMovement:true};
const env={world,system:{},saved,VARIANTS:{water:{id:'cookiedookie:water_creeper',move:'water'},lava:{id:'cookiedookie:lava_creeper',move:'lava'},phantom:{id:'cookiedookie:phantom_creeper',move:'phantom'}},getConfig:()=>cfg,diag:()=>{}};
let source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n').replace(/^import .*;\s*$/gm,'').replace(/\bexport function\b/g,'function');
vm.runInNewContext(source,env);
function entity(typeId,init=false){const props={'cs:init':init},events=[];return {typeId,events,getDynamicProperty:k=>props[k],setDynamicProperty:(k,v)=>props[k]=v,triggerEvent:e=>events.push(e)};}
const fresh=entity('cookiedookie:water_creeper');saved.onSpawn({entity:fresh});assert.deepEqual(fresh.events,['cookiedookie:special_move_on']);
const loaded=entity('cookiedookie:water_creeper',true);saved.onLoad({entity:loaded});assert.deepEqual(loaded.events,['cookiedookie:special_move_on']);
const disabled=entity('cookiedookie:lava_creeper',true);saved.onLoad({entity:disabled});assert.deepEqual(disabled.events,['cookiedookie:special_move_off']);
const ordinary=entity('cookiedookie:moss_creeper',true);saved.onLoad({entity:ordinary});assert.equal(ordinary.events.length,0);
console.log('Movement reload: water/lava switches reapplied; ordinary creeper unchanged');''')
 r=subprocess.run(['node',str(q/'test_movement.cjs'),str(SRC/'entities.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Environmental Creeper abilities must query integer block positions from fractional entity locations.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_variant_ecology.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let tick,effect;const floorReads=[];
const mob={id:'moss-1',typeId:'cookiedookie:moss_creeper',location:{x:1.7,y:64.4,z:-2.2},dimension:null,addEffect:(...a)=>effect=a};
const dim={id:'minecraft:overworld',getEntities:()=>[mob]};mob.dimension=dim;
const player={location:{x:0,y:64,z:0},dimension:dim};
const env={world:{getPlayers:()=>[player]},system:{runInterval:f=>tick=f},VARIANTS:{moss:{id:'cookiedookie:moss_creeper'}},getConfig:()=>({variantEcology:true}),
 getBlockSafe:(d,p)=>{assert.ok(Number.isInteger(p.x)&&Number.isInteger(p.y)&&Number.isInteger(p.z),'fractional block lookup');floorReads.push({...p});return p.y===63?{typeId:'minecraft:moss_block'}:{typeId:'minecraft:air'}},diag:()=>{}};
let source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n').replace(/^import .*;\s*$/gm,'').replace(/\bexport const\b/g,'const');
vm.runInNewContext(source+';globalThis.abilityKeys=variantAbilityKeys;',env);assert.equal(env.abilityKeys.length,23,'not all 23 variants have environment profiles');tick();assert.ok(effect,'moss ecology ability did not apply');assert.equal(effect[0],'regeneration');assert.deepEqual(floorReads[0],{x:1,y:64,z:-3});assert.deepEqual(floorReads[1],{x:1,y:63,z:-3});
console.log('Variant ecology: fractional coordinates mapped to valid block cells; moss ability applied');''')
 r=subprocess.run(['node',str(q/'test_variant_ecology.cjs'),str(SRC/'variant_ecology.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Shared block helper normalizes player/entity Vector3 positions to containing cells.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_block_lookup.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('export function getBlockSafe('),end=source.indexOf('\nexport function belowOf',start);
assert(start>=0&&end>start,'shared block helper not found');
let actual;const dim={getBlock:p=>{assert.ok(Number.isInteger(p.x)&&Number.isInteger(p.y)&&Number.isInteger(p.z));actual=p;return p}};
const env={};vm.runInNewContext(source.slice(start,end).replace('export function','function')+';globalThis.read=getBlockSafe;',env);
assert.deepEqual({...env.read(dim,{x:1.7,y:64.4,z:-2.2})},{x:1,y:64,z:-3});
assert.deepEqual({...actual},{x:1,y:64,z:-3});
console.log('Block lookup: fractional coordinates floored correctly, including negative positions');''')
 r=subprocess.run(['node',str(q/'test_block_lookup.cjs'),str(SRC/'util.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Players contact a mature pod in their feet cell or directly under it.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_player_contact.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('function playerContactSpore('),end=source.indexOf('\nexport function tryDeposit',start);
assert(start>=0&&end>start,'player spore contact function missing');
const pods=new Map([['1,64,-3',{typeId:'cookiedookie:creeper_spores',permutation:{getState:()=>3}}]]);
const env={Math,isSpore:b=>b?.typeId==='cookiedookie:creeper_spores',getBlockSafe:(d,p)=>{assert.ok(Number.isInteger(p.x)&&Number.isInteger(p.y)&&Number.isInteger(p.z));return pods.get(`${p.x},${p.y},${p.z}`)}};
vm.runInNewContext(source.slice(start,end).replace('function playerContactSpore','function playerContactSpore')+';globalThis.contact=playerContactSpore;',env);
const pod=env.contact({}, {x:1.4,y:65.2,z:-2.4});assert.equal(pod?.typeId,'cookiedookie:creeper_spores');
console.log('Player pickup: mature spore underfoot is detected at fractional player coordinates');''')
 r=subprocess.run(['node',str(q/'test_player_contact.cjs'),str(SRC/'players.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Explicit in-world fixture commands cover all eight strains and a forced vanilla fuse.
tools=(SRC/'test_tools.js').read_text(encoding='utf-8');main=(SRC/'main.js').read_text(encoding='utf-8')
ok('"cs:test_spores"' in tools and '"cs:test_blast"' in tools and '"cs:inspect_spores"' in tools,'manual runtime test commands missing')
ok('knownPods(dim.id,player.location,64,2000)' in tools and 'counts[strain][age]++' in tools,'live strain/stage inspection is not wired to nearby block state')
ok('plantSpore(block,strain)' in tools and 'TEST_STRAIN_COUNT=8' in tools,'strain fixture does not cover all eight strains')
ok('FIXTURE_HEIGHTS=[0,...Array.from({length:32}' in tools and 'y:origin.y+off.y' in tools,'strain fixture cannot find ground beneath an elevated player')
ok('minecraft:creeper' in tools and 'minecraft:start_exploding' in tools,'vanilla explosion test is not forced')
ok('import "./test_tools.js"' in main,'test helpers are not loaded by the add-on')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_tools_runtime.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('const TEST_STRAIN_COUNT'),end=source.indexOf('\nworld.afterEvents.scriptEventReceive.subscribe',start);
assert(start>=0&&end>start,'test tool implementation boundaries missing');
const placed=[],events=[],messages=[];
const dim={id:'minecraft:overworld',getBlock(p){const x=Math.floor(p.x),y=Math.floor(p.y),z=Math.floor(p.z);return y===63?{typeId:'minecraft:grass_block',isSolid:true,isAir:false,location:{x,y,z}}:{typeId:'minecraft:air',isSolid:false,isAir:true,location:{x,y,z}}},spawnEntity(typeId,pos){events.push({typeId,pos});return{typeId,triggerEvent:e=>events.push(e)}}};
const player={dimension:dim,location:{x:0.5,y:80.2,z:0.5},sendMessage:m=>messages.push(m)};
const env={Math,world:{},getBlockSafe:(d,p)=>d.getBlock(p),belowOf:b=>dim.getBlock({x:b.location.x,y:b.location.y-1,z:b.location.z}),isFree:b=>b?.isAir===true,hasSupport:b=>b?.isSolid===true,plantSpore:(b,n)=>placed.push({loc:b.location,strain:n}),diag:()=>{}};
vm.runInNewContext(source.slice(start,end).replace(/export function/g,'function'),env);
assert.equal(env.placeStrainFixture(player),8);assert.deepEqual(placed.map(p=>p.strain),[0,1,2,3,4,5,6,7]);assert.ok(placed.every(p=>p.loc.y===64),'fixture failed to find a supported surface below the elevated player');
assert.equal(env.forceVanillaBlast(player),true);assert.equal(events[0].typeId,'minecraft:creeper');assert.equal(events[1],'minecraft:start_exploding');
console.log('Manual runtime helpers: planted all eight strains and triggered a vanilla Creeper fuse');''')
 r=subprocess.run(['node',str(q/'test_tools_runtime.cjs'),str(SRC/'test_tools.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# The live inspector must report actual nearby block states, grouped by strain and age.
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_spore_inspector.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=src.indexOf('export function inspectNearbySpores('),end=src.indexOf('\nworld.afterEvents.scriptEventReceive.subscribe',start);
assert(start>=0&&end>start,'spore inspector function missing');
const source=src.slice(start,end).replace('export function','function ');
const positions=[{x:1,y:64,z:1},{x:2,y:64,z:1},{x:3,y:64,z:1}],ages=[2,3,0],strains=[0,0,3],messages=[],diag=[];
const blocks=positions.map((p,i)=>({typeId:'cookiedookie:creeper_spores',permutation:{getState(k){return k==='age'?ages[i]:strains[i];}}}));
const env={STRAINS:[{name:'Common Spore'},{name:'Luminous Spore'},{name:'Toxic Spore'},{name:'Frost Spore'}],STATE_AGE:'age',STATE_STRAIN:'strain',knownPods:()=>positions,getBlockSafe:(d,p)=>blocks[positions.findIndex(q=>q.x===p.x)],isSpore:b=>b?.typeId==='cookiedookie:creeper_spores',diag:(...a)=>diag.push(a)};
vm.runInNewContext(source+';globalThis.inspect=inspectNearbySpores;',env);
const player={dimension:{id:'minecraft:overworld'},location:{x:0,y:64,z:0},sendMessage:m=>messages.push(m)};
const counts=env.inspect(player);assert.equal(counts[0][2],1);assert.equal(counts[0][3],1);assert.equal(counts[3][0],1);
assert(messages.some(m=>m.includes('Common Spore')&&m.includes('0 0 1 1')),'common strain stages were not displayed');assert(messages.some(m=>m.includes('Frost Spore')&&m.includes('1 0 0 0')),'frost strain stage was not displayed');assert.equal(diag[0][1].nearby,3);
console.log('Spore inspector: nearby strain and stage counts reflect block state');''')
 r=subprocess.run(['node',str(q/'test_spore_inspector.cjs'),str(SRC/'test_tools.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Authored ruins cover three distinct layouts and reject unsafe sites before writing.
ruins=(SRC/'field_ruins.js').read_text(encoding='utf-8')
ok('RUIN_DESIGNS=[' in ruins and 'moss_stones' in ruins and 'field_markers' in ruins,'three authored ruin layouts missing')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_ruins.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('export const RUIN_DESIGNS=['),end=source.indexOf('system.runInterval',start);
assert(start>=0&&end>start,'ruin design/safety functions missing');
const env={inZone:()=>false,hasSupport:b=>b?.typeId==='minecraft:grass_block',knownPlayerPlaced:()=>false,getBlockSafe:(d,p)=>{const k=`${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`;if(d.blocked===k)return{typeId:'minecraft:stone',isAir:false,location:p};if(Math.floor(p.y)===-1)return{typeId:'minecraft:grass_block',isAir:false,location:p};return{typeId:'minecraft:air',isAir:true,location:p}}};
const code=source.slice(start,end).replace(/export const /g,'const ').replace(/export function /g,'function ');
const guard=fs.readFileSync(process.argv[3],'utf8').replace(/^import .*$/m,'').replace(/^export /gm,'');
env.zoneHit=false;env.inZone=()=>env.zoneHit;vm.createContext(env);vm.runInContext(guard,env);
vm.runInContext(code+';globalThis.designs=RUIN_DESIGNS;globalThis.check=validRuinSite;',env);
assert.equal(env.designs.length,3);const dim={id:'minecraft:overworld'};const c={x:0,y:0,z:0};
for(const d of env.designs)assert.equal(env.check(dim,c,d.blocks),true,`valid design ${d.id} rejected`);
dim.blocked='0,-1,0';assert.equal(env.check(dim,c,env.designs[1].blocks),false,'solid site was accepted');
dim.blocked='';env.zoneHit=true;assert.equal(env.check(dim,c,env.designs[0].blocks),false,'quarantined site was accepted');
console.log('Spore ruins: all three layouts validate; solid and quarantined sites are rejected');''')
 r=subprocess.run(['node',str(q/'test_ruins.cjs'),str(SRC/'field_ruins.js'),str(SRC/'structure_guard.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Every custom Creeper variant has a distinct data-driven blast-effect profile.
data=(SRC/'generated_data.js').read_text(encoding='utf-8');va=data.index('export const VARIANTS = ')+len('export const VARIANTS = ');vb=data.index(';',va);variants=json.loads(data[va:vb])
ok(len(variants)==23,'variant count changed')
ok(all(v.get('effect') for v in variants.values()),'one or more Creeper variants lacks a blast effect profile')
blast_source=(SRC/'explosions.js').read_text(encoding='utf-8')
ok('if (def?.effect) applyEffect(dim, loc, def.effect);' in blast_source,'variant blast effect payload is not applied')
# Creeper-family blasts must create visible stage-0 seeds on valid nearby surfaces.
logic=(SRC/'logic.js').read_text();blast=(SRC/'explosions.js').read_text()
ok('typeId === "minecraft:creeper"' in logic,'vanilla creeper blast source is not recognized')
ok('subscribeBlastSignal(world.beforeEvents?.explosion, "before")' in blast and 'subscribeBlastSignal(world.afterEvents?.explosion, "after")' in blast,'blast handler must subscribe to both event phases')
ok('blast_missing_source_${phase}' in blast and 'recentlyHandledBlasts' in blast,'blast source fallback or cross-phase dedupe is missing')
ok('blast_visible_seeded' in blast and 'blast_no_valid_surface' in blast,'blast outcomes are not diagnosed')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_blast_hook.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('const recentlyHandledBlasts'),end=source.indexOf('\nfunction release(',start);
assert(start>=0&&end>start,'explosion event handler boundaries not found');
let queued=0;const diagnostics=[];
const env={beforeHook:null,afterHook:null,world:{beforeEvents:{explosion:{subscribe:f=>env.beforeHook=f}},afterEvents:{explosion:{subscribe:f=>env.afterHook=f}}},system:{currentTick:10,run:f=>queued++},variantFromTypeId:id=>id==='minecraft:creeper'?{key:null,def:null}:undefined,diag:(...a)=>diagnostics.push(a)};
vm.runInNewContext(source.slice(start,end).replace(/export function/g,'function'),env);
assert.equal(typeof env.beforeHook,'function','before-explosion handler did not subscribe');
assert.equal(typeof env.afterHook,'function','after-explosion fallback did not subscribe');
const src={typeId:'minecraft:creeper',location:{x:0,y:1,z:0},hasComponent:()=>false,getDynamicProperty:()=>undefined};
const dimension={id:'minecraft:overworld'};
env.beforeHook({source:undefined,dimension});
env.afterHook({source:src,dimension});
assert.equal(queued,1,'after phase failed to rescue a missing before-event source');
const second={...src,location:{x:5,y:1,z:0}};
env.beforeHook({source:second,dimension});
env.afterHook({source:second,dimension});
assert.equal(queued,2,'same blast was not deduplicated across event phases');
env.system.currentTick=15;env.afterHook({source:src,dimension});
assert.equal(queued,3,'later blast at the same location was incorrectly suppressed');
console.log('Blast event phases: missing-source fallback and cross-phase deduplication passed');''')
 r=subprocess.run(['node',str(q/'test_blast_hook.cjs'),str(SRC/'explosions.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
ok('seedVisibleFromBlast(dim, loc, radius, srcStrain, biome, cfg, visibleCap)' in blast,'blast handler does not seed visible growth')
ok('germinate(block, strain, 3)' in blast and 'larger, visible stage-3 spore after the blast' in (SRC/'test_tools.js').read_text(),'blast path or in-game test prompt does not use the larger visible stage')
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'test_blast.cjs').write_text(r'''const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('function release('),end=source.indexOf('function applyEffect(');
assert(start>=0&&end>start,'blast implementation boundaries not found');
const code=source.slice(start,end);
function smoke(charged){
 const planted=new Set(),made=[];
 const math=Object.create(Math);math.random=()=>0.99;
 const cfg={radiusNormal:2,radiusCharged:2,maxPlacementsPerBlast:24,depositChance:0,barriersEnabled:false,deepDarkBlocksNatural:false,mutationChance:0,mutationOutcomes:126};
 const dim={id:'minecraft:overworld',getBlock(p){const x=Math.floor(p.x),y=Math.floor(p.y),z=Math.floor(p.z),key=`${x},${y},${z}`;
  if(planted.has(key))return {typeId:'cookiedookie:creeper_spores',isAir:false,isSolid:false,location:{x,y,z}};
  if(y===-1)return {typeId:'minecraft:grass_block',isAir:false,isSolid:true,location:{x,y,z}};
  return {typeId:'minecraft:air',isAir:true,isSolid:false,isWaterlogged:false,location:{x,y,z}};
 }};
 const env={Math:math,getConfig:()=>cfg,getBiomeId:()=>undefined,getBlockSafe:(d,p)=>d.getBlock(p),belowOf:b=>dim.getBlock({x:b.location.x,y:b.location.y-1,z:b.location.z}),isFree:b=>b.isAir||b.typeId==='minecraft:water',hasSupport:b=>b.isSolid,blockedBetween:()=>false,inZone:()=>false,pickStrain:()=>0,diag:()=>{},germinate:(b,strain,age=0)=>{const p=b.location;planted.add(`${p.x},${p.y},${p.z}`);made.push({loc:p,strain,age});},addPending:()=>true};
 vm.runInNewContext(code+';globalThis.release=release;',env);
 env.release({dim,loc:{x:0.5,y:0.5,z:0.5},charged,srcStrain:0,def:null});return made;
}
const normal=smoke(false),charged=smoke(true);
assert.equal(normal.length,1,'normal creeper blast leaves one visible seed');
assert.equal(charged.length,2,'charged creeper blast leaves two visible seeds');
assert(normal.every(p=>p.age===3),'blast seeds must start at the larger visible age-3 stage');
assert(charged.every(p=>p.age===3),'charged blast seeds must start at the larger visible age-3 stage');
console.log('Blast germination: normal=1 and charged=2 larger age-3 seeds');''')
 r=subprocess.run(['node',str(q/'test_blast.cjs'),str(SRC/'explosions.js')],capture_output=True,text=True)
 ok(r.returncode==0,r.stdout+'\n'+r.stderr)
 print(r.stdout.strip())
# Validate optional native feature rules from this source package and supported biome tags.
opt=BASE/'optional_worldgen_pack'
feat=json.loads((opt/'features/spore_nest_native.json').read_text())['minecraft:single_block_feature']
ok(feat['places_block']=='cookiedookie:spore_nest','optional worldgen block')
expected_tags={'forest','jungle','plains','taiga','swamp','desert','savanna','mesa','mangrove_swamp','cherry_grove','mooshroom_island','frozen'}
found=set()
for p in (opt/'feature_rules').glob('*.json'):
 f=json.loads(p.read_text())['minecraft:feature_rules']
 ok(f['description']['places_feature']==feat['description']['identifier'],'rule references missing feature')
 ok(f['description']['identifier'].split(':',1)[1]==p.stem,'rule identifier does not match filename')
 found.add(f['conditions']['minecraft:biome_filter']['value'])
ok(found==expected_tags,f'optional biome rule coverage mismatch: {found}')
import tests_0_8_31_fixes
tests_0_8_31_fixes.run(ok,BASE)
tests_0_8_31_fixes.run_round2(ok,BASE)
tests_0_8_31_fixes.run_trails(ok,BASE)
tests_0_8_31_fixes.run_protected(ok,BASE)
print(f'PASS {check} offline checks. These offline checks do not cover Minecraft Bedrock runtime; see 0_8_31_BEDROCK_TESTS.txt for the separate PC smoke test.')



