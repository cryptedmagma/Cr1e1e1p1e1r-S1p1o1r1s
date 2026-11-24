"""0.8.31 regression checks for the reported-defect fixes (run by test_0_8_31.py).

Offline/mocked only. These exercise the pure rules and source wiring; they do not prove
Bedrock runtime behaviour, which still needs an in-game check.
"""
import json, subprocess, tempfile
from pathlib import Path


def run(ok, BASE):
    SRC = BASE / 'behavior_pack' / 'scripts'
    RP = BASE / 'resource_pack'

    def node(name, code, *args):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / name
            f.write_text(code, encoding='utf-8')
            r = subprocess.run(['node', str(f), *map(str, args)], capture_output=True, text=True)
            ok(r.returncode == 0, f'{name} failed: {r.stderr[-600:]}')
            return r.stdout

    # --- Mob carriers: reload-safe active-time window, unchanged thresholds -------------------
    out = node('carrier_rules.cjs', r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/^export /gm,'');
const ctx={};vm.createContext(ctx);vm.runInContext(src+';this.R={CARRY_DURATION,makeCarrier,validCarrier,tickCarrier,carriedTicks,dropEligible,dripEligible,attemptDripRoll,upgradeCarrier,canHostDeathSpore};',ctx);
const R=ctx.R, cfg={};
assert.equal(R.CARRY_DURATION,2400,'carry window length must stay 2400 ticks');
// Pick up at world tick 1000, carried 200 active ticks, then the world is closed for a long time.
const c=R.makeCarrier(3,{x:0.5,y:64,z:0.5},1000,'minecraft:overworld');
assert.equal(c.activeTicks,0);
for(let i=0;i<10;i++)R.tickCarrier(c,1000+i*20,20);
assert.equal(R.carriedTicks(c,999999),200);
assert(R.validCarrier(c,1000000),'carrier must survive a reload/unload gap of absolute time');
assert(R.validCarrier(c,5),'carrier must survive /time changes that move absolute time backwards');
// The 40-tick minimum and 20-block final threshold still gate the final drop.
c.distance=19.9; assert(!R.dropEligible(c,2000000,{},cfg),'below 20 blocks must not drop');
c.distance=20;   assert(R.dropEligible(c,2000000,{},cfg),'20 blocks + >=40 active ticks must drop');
const young=R.makeCarrier(1,{x:0,y:64,z:0},50,'o'); young.distance=25; R.tickCarrier(young,50,20);
assert(!R.dropEligible(young,999999,{},cfg),'fewer than 40 carried ticks must not drop even after a long gap');
// One 40% drip roll at 15 blocks; a roll never repeats.
const d=R.makeCarrier(2,{x:0,y:0,z:0},0,'o'); d.distance=14.9; assert(!R.dripEligible(d,cfg));
d.distance=15; assert(R.dripEligible(d,cfg)); assert.equal(R.attemptDripRoll(d,cfg,()=>0.39),true);
assert(!R.dripEligible(d,cfg),'drip roll must be one-time');
const e=R.makeCarrier(2,{x:0,y:0,z:0},0,'o'); e.distance=15; assert.equal(R.attemptDripRoll(e,cfg,()=>0.40),false,'40% boundary');
// The window still ends after 2400 active ticks.
const f=R.makeCarrier(0,{x:0,y:0,z:0},0,'o'); R.tickCarrier(f,0,2400); assert(R.validCarrier(f,0)); R.tickCarrier(f,0,20); assert(!R.validCarrier(f,0));
// Legacy (pre-0.8.31) saved carriers keep their absolute window, then adopt active time.
const L={strain:4,origin:{x:0,y:0,z:0},acquired:100,expires:2500,distance:0};
assert(R.validCarrier(L,2000)); assert(!R.validCarrier(L,2600));
R.tickCarrier(L,1100,20); assert.equal(L.activeTicks,1020);
// Death deposits can push through soft ground cover; stone cannot be replaced.
assert(R.canHostDeathSpore('minecraft:short_grass')&&R.canHostDeathSpore('minecraft:snow_layer'));
assert(!R.canHostDeathSpore('minecraft:stone')&&!R.canHostDeathSpore('minecraft:chest'));
console.log('carrier ok');
''', SRC / 'mob_carrier_rules.js')
    ok('carrier ok' in out, 'carrier rule regression did not complete')

    eco = (SRC / 'ecology.js').read_text(encoding='utf-8')
    ok('tickCarrier(c,now,20);' in eco, 'mob carrier scan must advance the saved active-time window')
    ok('(isDeath && canHostDeathSpore(b.typeId))' in eco, 'death deposit must accept soft ground cover')
    ok(eco.count('world.afterEvents.entityDie.subscribe') == 1 and 'handledDeaths.has(id)' in eco, 'mob death release must stay single and deduplicated')

    # --- Player carriers: saved on the player, counted in active ticks, released on death ------
    pl = (SRC / 'players.js').read_text(encoding='utf-8')
    start = pl.index('export function decodePlayerCarry('); end = pl.index('\nfunction saveCarry(', start)
    out = node('player_carry.cjs', r'''
const vm=require('node:vm'),assert=require('node:assert/strict');
const code=process.argv[2].replace(/^export /gm,'');
const ctx={};vm.createContext(ctx);vm.runInContext('const PLAYER_CARRY_TICKS=2400;'+code+';this.d=decodePlayerCarry;',ctx);
const d=ctx.d;
assert.deepEqual(JSON.parse(JSON.stringify(d(JSON.stringify({strain:5,left:2,remaining:900})))),{strain:5,left:2,remaining:900});
assert.equal(d(JSON.stringify({strain:9,left:2,remaining:900})),null,'bad strain');
assert.equal(d(JSON.stringify({strain:1,left:0,remaining:900})),null,'spent carrier');
assert.equal(d(JSON.stringify({strain:1,left:2,remaining:0})),null,'expired carrier');
assert.equal(d('not json'),null); assert.equal(d(undefined),null);
assert.equal(d(JSON.stringify({strain:1,left:9,remaining:99999})).left,3,'left is clamped to the approved 3 deposits');
console.log('player ok');
''', pl[start:end])
    ok('player ok' in out, 'player carrier decode regression did not complete')
    ok('const c = loadCarry(p);' in pl and 'c.remaining -= 20;' in pl, 'player carrier must reload saved state and count active ticks')
    ok('expires: now + 2400' not in pl, 'player carrier must not depend on the per-session tick counter')
    ok('typeId !== "minecraft:player"' in pl and 'dropCarry(p);' in pl and 'tryDeposit(dim,' in pl, 'player death release missing')

    # --- Spore-Proof armor: one ability per piece ---------------------------------------------
    out = node('armor.cjs', r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8').replace(/^export /gm,'');
const ctx={};vm.createContext(ctx);vm.runInContext(src+';this.f=piecesBlockEffect;this.B=PIECE_BLOCKS;',ctx);
const f=ctx.f, none={}, H={Head:'cookiedookie:spore_helmet'}, C={Chest:'cookiedookie:spore_chestplate'},
      L={Legs:'cookiedookie:spore_leggings'}, F={Feet:'cookiedookie:spore_boots'};
assert(f(H,'blindness')&&f(H,'nausea')&&f(H,'darkness')&&!f(H,'poison'));
assert(f(C,'poison')&&f(C,'hunger')&&!f(C,'slowness'));
assert(f(L,'slowness')&&!f(L,'weakness'));
assert(f(F,'weakness')&&!f(F,'blindness'));
assert(!f(none,'poison')&&!f({Head:'minecraft:iron_helmet'},'blindness'),'vanilla armor grants nothing');
assert(!f({Head:'cookiedookie:spore_boots'},'blindness'),'a piece only works in its own slot');
for(const fx of ['regeneration']) assert(!f({...H,...C,...L,...F},fx),'beneficial effects are never blocked');
const all=new Set(Object.values(ctx.B).flat()); assert.equal(all.size,7,'four pieces cover seven distinct effects');
console.log('armor ok');
''', SRC / 'protection.js')
    ok('armor ok' in out, 'armor ability regression did not complete')
    ex = (SRC / 'explosions.js').read_text(encoding='utf-8')
    ok('armorBlocksEffect(e, eff.name)' in ex, 'blast effects must consult per-piece armor')
    prot = (SRC / 'protection.js').read_text(encoding='utf-8')
    ok('export function hasSporeProtection(player) {return protectionPieces(player)>0;}' in prot, 'approved any-piece poison rule changed')

    # --- Hybrid plants: four distinct, in-bounds stages per plant -------------------------------
    for name in ('spore_bluebell', 'spore_bracken', 'spore_bogcap'):
        sizes, shapes = [], []
        tex = RP / f'textures/blocks/hybrids/{name}.png'
        raw = tex.read_bytes(); tw, th = int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')
        for n in range(4):
            g = json.loads((RP / f'models/blocks/{name}.age_{n}.geo.json').read_text())['minecraft:geometry'][0]
            d = g['description']
            ok(d['identifier'] == f'geometry.{name}.age_{n}', f'{name} stage {n} identifier')
            ok((d['texture_width'], d['texture_height']) == (tw, th), f'{name} stage {n} texture size must match the atlas')
            cubes = [c for b in g['bones'] for c in b.get('cubes', [])]
            for c in cubes:
                for face, uv in c['uv'].items():
                    u, v = uv['uv']; w, h = uv['uv_size']
                    ok(0 <= u and 0 <= v and u + w <= tw and v + h <= th, f'{name} stage {n}: {face} UV leaves the texture')
                ok(all(abs(c['origin'][i]) <= 8 and abs(c['origin'][i] + c['size'][i]) <= 8 for i in (0, 2)), f'{name} stage {n}: part outside the block footprint')
                ok(c['origin'][1] >= 0 and c['origin'][1] + c['size'][1] <= 16, f'{name} stage {n}: part outside block height')
            sizes.append(max(c['origin'][1] + c['size'][1] for c in cubes))
            shapes.append(json.dumps(sorted((c['origin'], c['size']) for c in cubes)))
        ok(sizes == sorted(sizes) and sizes[0] < sizes[3], f'{name}: stages must grow taller')
        ok(len(set(shapes)) == 4, f'{name}: four visibly different stages required')
    plant_shapes = {name: (RP / f'models/blocks/{name}.age_3.geo.json').read_text() for name in ('spore_bluebell', 'spore_bracken', 'spore_bogcap')}
    ok(len({json.dumps(json.loads(t)['minecraft:geometry'][0]['bones']) for t in plant_shapes.values()}) == 3, 'the three hybrids must not share one model')


def run_round2(ok, BASE):
    """Carrier audit (logging, spectators, inspection) and structure placement safeguards."""
    SRC = BASE / 'behavior_pack' / 'scripts'
    pl = (SRC / 'players.js').read_text(encoding='utf-8')
    eco = (SRC / 'ecology.js').read_text(encoding='utf-8')
    ok('!isSpectator(p)' in pl and 'export function isSpectator(p)' in pl, 'spectators must never become carriers')
    ok('player_spore_death_released' in pl and 'player_spore_death_no_valid_cell' in pl, 'player death release outcome must be logged')
    ok('mob_spore_death_no_valid_cell' in eco, 'mob death fallback reason must be logged')
    ok('ev.id !== "cs:carrier"' in pl and 'getDynamicProperty("cs:mob_spore_061")' in pl, '/scriptevent cs:carrier inspection missing')
    ok(pl.count('world.afterEvents.entityDie.subscribe') == 1, 'player death release must be a single subscription')
    # Structure safeguards: pure rule, plus both placers wired through it.
    src = (SRC / 'structure_guard.js').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / 'guard.cjs'
        f.write_text(r'''
const vm=require('node:vm'),assert=require('node:assert/strict');
const code=process.argv[2].replace(/^import .*$/m,'').replace(/^export /gm,'');
const zones=new Set(['minecraft:overworld:5:64:5']);
const ctx={inZone:(d,p)=>zones.has(`${d}:${p.x}:${p.y}:${p.z}`)};vm.createContext(ctx);
vm.runInContext(code+';this.P=cellIsProtected;this.S=safeStructureCell;',ctx);
for(const t of ['minecraft:chest','minecraft:barrel','minecraft:wheat','minecraft:carrots','cookiedookie:creeper_spores','minecraft:red_shulker_box','minecraft:farmland'])assert(ctx.P(t),t);
assert(!ctx.P('minecraft:air')&&!ctx.P('minecraft:grass_block'));
const dim={id:'minecraft:overworld'},air=(x,y,z)=>({isAir:true,typeId:'minecraft:air',x,y,z});
assert(ctx.S(dim,air(0,64,0)),'plain air is fine');
assert(!ctx.S(dim,air(5,64,5)),'quarantined air is refused');
assert(!ctx.S(dim,{isAir:false,typeId:'minecraft:chest',x:1,y:64,z:1}),'containers are never overwritten');
assert(!ctx.S(dim,null));
console.log('guard ok');''', encoding='utf-8')
        r = subprocess.run(['node', str(f), src], capture_output=True, text=True)
        ok(r.returncode == 0 and 'guard ok' in r.stdout, f'structure guard regression failed: {r.stderr[-400:]}')
    fr = (SRC / 'field_ruins.js').read_text(encoding='utf-8')
    se = (SRC / 'structure_encounters.js').read_text(encoding='utf-8')
    ok(fr.count('safeStructureCell(dim,b)') == 2, 'micro-ruins must check every cell at validation and write time')
    ok('safeStructureCell(dim,at)' in se, 'structure (village) nests must respect quarantine and protected blocks')


def run_trails(ok, BASE):
    """Walking trails / orbiting bubbles: every reference resolves, and the removed parts are gone."""
    RP = BASE / 'resource_pack'
    particles = {}
    for p in (RP / 'particles').glob('*.particle.json'):
        doc = json.loads(p.read_text())
        particles[doc['particle_effect']['description']['identifier']] = doc
    sprite = RP / 'textures/particle/cs_trails.png'
    ok(sprite.is_file(), 'trail sprite sheet missing')
    anims = json.loads((RP / 'animations/variant_trails.animation.json').read_text())['animations']
    ok(set(anims) == {'animation.cookiedookie.walk_trail', 'animation.cookiedookie.orbit_particles'}, 'trail animations missing')
    expect = {'water': {'trail', 'orbit'}, 'glowing': {'trail'}, 'flower': {'trail'}, 'lava': {'trail'},
              'mushroom': {'trail'}, 'spore_queen': {'trail'}}
    for key in ('moss', 'cave', 'crystal', 'swamp', 'desert', 'snow', 'jungle', 'mushroom', 'sculk', 'nether', 'end', 'water',
                'lava', 'flower', 'thorn', 'phantom', 'giant', 'miniature', 'glowing', 'spore_queen', 'grass_crown',
                'carved_wood', 'slender_green'):
        d = json.loads((RP / f'entity/{key}_creeper.entity.json').read_text())['minecraft:client_entity']['description']
        fx = d.get('particle_effects', {})
        ok(set(fx) == expect.get(key, set()), f'{key}: unexpected particle effects {sorted(fx)}')
        for kind, ident in fx.items():
            doc = particles.get(ident)
            ok(doc is not None, f'{key}: particle {ident} has no particle file')
            if doc:
                ok(doc['particle_effect']['description']['basic_render_parameters']['texture'] == 'textures/particle/cs_trails', f'{ident}: wrong texture')
                u = doc['particle_effect']['components']['minecraft:particle_appearance_billboard']['uv']
                from PIL import Image as _I
                sw, sh = _I.open(sprite).size
                ok(u['texture_width'] == sw and u['texture_height'] == sh, f'{ident}: uv size must match the {sw}x{sh} sprite sheet')
                ok(not isinstance(u['uv'][0], (int, float)) or 0 <= u['uv'][0] < sw, f'{ident}: uv outside sheet')
                ok(u['uv_size'][0] <= sh and u['uv_size'][1] <= sh, f'{ident}: sprite frame taller than the sheet')
        animate = d['scripts']['animate']
        ok(('trail' in fx) == ({'walk_trail': 'query.modified_move_speed > 0.05'} in animate), f'{key}: trail must play only while walking')
        ok(('orbit' in fx) == ('orbit_particles' in animate), f'{key}: orbit wiring')
        ok(animate[:2] == ['legs', 'idle_ambient'], f'{key}: original leg/breathing animations must still run first')
        if fx:
            geo = json.loads((RP / f'models/entity/{key}_creeper.geo.json').read_text())['minecraft:geometry'][0]
            body = next(b for b in geo['bones'] if b['name'] == 'body')
            ok(set(fx) <= set(body.get('locators', {})), f'{key}: particle locator missing on body bone')
    # Removed by request: seaweed and bubble blocks (water), glow cubes (glowing), foot mushrooms (mushroom, queen).
    def cubes(key, bone=None):
        g = json.loads((RP / f'models/entity/{key}_creeper.geo.json').read_text())['minecraft:geometry'][0]
        return [c for b in g['bones'] if bone in (None, b['name']) for c in b.get('cubes', [])]
    # Water was fully redrawn (lily pad hat + water lily); no seaweed or bubble blocks remain on the model.
    wb = {b['name'] for b in json.loads((RP / 'models/entity/water_creeper.geo.json').read_text())['minecraft:geometry'][0]['bones']}
    ok({'lily_pad', 'lily_flower'} <= wb, 'water creeper should wear the lily pad and water lily')
    ok(all(len(cubes('water', leg)) == 1 for leg in ('leg0', 'leg1', 'leg2', 'leg3')) and len(cubes('water', 'body')) == 1,
       'water creeper legs/body must carry no seaweed or bubble blocks')
    wt = json.loads((RP / 'particles/cs_trail_water.particle.json').read_text())['particle_effect']['components']
    ok(wt['minecraft:particle_appearance_billboard']['facing_camera_mode'] == 'emitter_transform_xz', 'lily pad trail must lie flat')
    ob = json.loads((RP / 'particles/cs_orbit_bubbles.particle.json').read_text())['particle_effect']['components']
    ok(ob['minecraft:emitter_rate_steady']['max_particles'] == 4, 'about four bubbles at a time around the water creeper')
    ok('particle_age' in str(ob['minecraft:particle_appearance_tinting']['color'][3]), 'bubbles must fade out')
    ok(len(cubes('glowing')) == 6, 'glowing creeper should be just the base body now (glow motes are a trail)')
    for key in ('mushroom', 'spore_queen'):
        for leg in ('leg0', 'leg1', 'leg2', 'leg3'):
            ok(len(cubes(key, leg)) == 1, f'{key}: {leg} should hold only the foot (mushrooms became a trail)')


def run_protected(ok, BASE):
    """2026-11-23 full redo of Swamp, Crystal, Jungle, Lava, Thorn and Spore Queen: protected parts unchanged,
    vanilla rig unchanged, and every signature part of the concept target present as its own bone."""
    import numpy as np
    from PIL import Image as _I
    RP = BASE / 'resource_pack'
    PROT = BASE / 'creeper_forge' / 'protected'
    def geo(path):
        return json.loads(path.read_text())['minecraft:geometry'][0]
    rig = {'body': [0.0, 6.0, 0.0], 'head': [0.0, 18.0, 0.0], 'leg0': [-2.0, 6.0, 4.0], 'leg1': [2.0, 6.0, 4.0],
           'leg2': [-2.0, 6.0, -4.0], 'leg3': [2.0, 6.0, -4.0]}
    parts = {'swamp': ('lily_pad', 'lotus'), 'crystal': ('crystal_crown',), 'jungle': ('canopy',), 'lava': ('molten_crown',),
             'thorn': ('thorn_wreath',), 'spore_queen': ('cap',)}
    for key, need in parts.items():
        g = geo(RP / f'models/entity/{key}_creeper.geo.json')
        bones = {b['name']: b for b in g['bones']}
        for name, pv in rig.items():
            ok(name in bones and bones[name]['pivot'] == pv and 'rotation' not in bones[name], f'{key}: vanilla rig bone {name} changed')
        ok(bones['head'].get('parent') == 'body', f'{key}: head must stay parented to body')
        hc = bones['head']['cubes'][0]
        ok(hc['origin'] == [-4.0, 18.0, -4.0] and hc['size'] == [8.0, 8.0, 8.0], f'{key}: the 8x8x8 head moved or changed size')
        for n in need:
            ok(n in bones and bones[n].get('parent') in ('head', 'lily_pad'), f'{key}: signature part {n} missing')
    # protected parts are byte-for-byte the previous build: same cube geometry and the same pixels on every face
    keep = {'thorn': [('head', [-4, 18, -4], [8, 8, 8])],
            'spore_queen': [('body', [-5, 0, 2], [10, 17.5, 1]), ('body', [-4.5, 0, 3.2], [9, 12, 1]), ('body', [4, 0, -2], [1, 17.5, 6]),
                            ('body', [5.2, 0, -1], [1, 11, 6]), ('body', [-5, 0, -1], [1, 16, 5]), ('body', [-7, 0, 4], [14, 1.2, 8]),
                            ('body', [5, 0, -3], [6, 1.2, 9]), ('leg0', [-4, 0, 2], [4, 6, 4]), ('leg1', [0, 0, 2], [4, 6, 4]),
                            ('leg2', [-4, 0, -6], [4, 6, 4]), ('leg3', [0, 0, -6], [4, 6, 4])]}
    for key, plist in keep.items():
        og, ng = geo(PROT / f'{key}_creeper.geo.json'), geo(RP / f'models/entity/{key}_creeper.geo.json')
        oi = np.array(_I.open(PROT / f'{key}_creeper.png').convert('RGBA'))
        ni = np.array(_I.open(RP / f'textures/entity/cookiedookie/{key}_creeper.png').convert('RGBA'))
        def find(g, bone, origin, size):
            for b in g['bones']:
                if b['name'] == bone:
                    for c in b.get('cubes', []):
                        if c['origin'] == [float(v) for v in origin] and c['size'] == [float(v) for v in size]:
                            return c
        for bone, origin, size in plist:
            oc, nc = find(og, bone, origin, size), find(ng, bone, origin, size)
            ok(oc is not None and nc is not None, f'{key}: protected part {bone} {origin} missing')
            if oc is None or nc is None:
                continue
            ok(oc.get('rotation') == nc.get('rotation') and oc.get('pivot') == nc.get('pivot'), f'{key}: protected part {bone} {origin} moved')
            ok(set(oc['uv']) == set(nc['uv']), f'{key}: protected part {bone} {origin} faces changed')
            for face in oc['uv']:
                (ox, oy), (w, h) = oc['uv'][face]['uv'], oc['uv'][face]['uv_size']
                (nx, ny), (w2, h2) = nc['uv'][face]['uv'], nc['uv'][face]['uv_size']
                same = (w, h) == (w2, h2) and np.array_equal(oi[int(oy):int(oy + h), int(ox):int(ox + w)], ni[int(ny):int(ny + h), int(nx):int(nx + w)])
                ok(same, f'{key}: protected part {bone} {origin} {face} pixels changed')
