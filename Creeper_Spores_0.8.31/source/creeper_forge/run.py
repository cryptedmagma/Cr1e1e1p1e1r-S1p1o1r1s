"""Generate creeper assets into the resource pack and render Blockbench previews beside the reference art."""
import sys, json, pathlib
from PIL import Image
import forge, designs
ROOT = pathlib.Path(__file__).resolve().parent.parent
RP = ROOT / 'resource_pack'
PREV = ROOT / '_previews'; PREV.mkdir(exist_ok=True)
REF = json.loads((ROOT / 'reference_art/manifest.json').read_text())
REF_BY_KEY = {v['entity_key']: ROOT / 'reference_art' / k for k, v in REF.items()}

def generate(key):
    m, opts = designs.DESIGNS[key]()
    if 'bounds' in opts: m.bounds = opts['bounds']
    geo, img = m.build(seed=opts.get('seed', 11))
    import designs_redo
    img = designs_redo.apply_keep(geo, img, opts)  # protected parts copied exactly from tools/protected/
    (RP / f'models/entity/{key}_creeper.geo.json').write_text(json.dumps(geo, indent=1))
    t = RP / 'textures/entity/cookiedookie'
    img.save(t / f'{key}_creeper.png')
    alt = forge.tint(img, *opts.get('alt', ((0.88, 0.92, 0.88), (0, 0, 0))))
    alt.save(t / f'{key}_creeper_alt.png')
    forge.charge(img, 3).save(t / f'{key}_creeper_charged.png')
    forge.charge(alt, 5).save(t / f'{key}_creeper_alt_charged.png')
    # glowing variants use Bedrock's emissive-alpha entity material; others keep the vanilla creeper material
    ent = RP / f'entity/{key}_creeper.entity.json'
    e = json.loads(ent.read_text())
    e['minecraft:client_entity']['description']['materials']['default'] = 'entity_emissive_alpha' if m.glow else 'creeper'
    ent.write_text(json.dumps(e, indent=2))
    import trails
    trails.wire(key)  # walking trails / orbiting particles (cosmetic, client-side)
    # opaque copy for the Blockbench preview (Blockbench shows low alpha as see-through)
    prev = img.copy(); prev.putalpha(255); prev.save(PREV / f'{key}_preview_tex.png')
    return geo, img

def render(key, cam=None):
    import bb, preview
    preview.load(str(RP / f'models/entity/{key}_creeper.geo.json'), str(PREV / f'{key}_preview_tex.png'))
    try:
        bb.tool('create_offscreen_view', id='shot', width=480, height=600, antialias=False, copy_view='none')
    except Exception:
        pass
    m, opts = designs.DESIGNS[key]()
    pos, tgt = opts.get('cam', ([-34, 32, -46], [0, 14, 0]))
    r = bb.tool('set_camera_angle', view='shot', position=pos, target=tgt, projection='perspective', fov=opts.get('fov', 38))
    p = bb.save_images(r, str(PREV / f'{key}_render'))[0]
    # side-by-side with the reference
    a = Image.open(p).convert('RGB'); b = Image.open(REF_BY_KEY[key]).convert('RGB')
    b = b.resize((int(b.width * a.height / b.height), a.height))
    out = Image.new('RGB', (a.width + b.width, a.height), (40, 40, 52)); out.paste(a, (0, 0)); out.paste(b, (a.width, 0))
    out.save(PREV / f'{key}_compare.png')
    return PREV / f'{key}_compare.png'

if __name__ == '__main__':
    keys = sys.argv[1:] or list(designs.DESIGNS)
    for k in keys:
        geo, img = generate(k)
        print(k, 'tex', img.size, 'cubes', sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones']), '->', render(k))
