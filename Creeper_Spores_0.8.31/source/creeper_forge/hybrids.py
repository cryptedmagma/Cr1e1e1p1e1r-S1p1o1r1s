"""Hybrid plants (Spore Bluebell, Spore Bracken, Spore Bogcap): four distinct growth stages each.

All four stages of one plant share one texture atlas (the block uses a single texture), so the
stages are built together as bones age0..age3 of one Model, then split into one geometry file
per stage. Every face gets its own UV region inside the atlas (the old models overflowed a 16x16
texture). Cube rotations stay on a single axis in 22.5-degree steps to suit block geometry.
"""
import json, pathlib, sys
from forge import Model, Mat, cover_top, spots, pal

ROOT = pathlib.Path(__file__).resolve().parent.parent
RP = ROOT / 'resource_pack'

STEM = ('#3f6e22', '#4f8228', '#5f9430')
LEAF = ('#4a8a2a', '#5ea034', '#72b440', '#86c44c')


def stage(m, n):
    return m.bone(f'age{n}', [0, 0, 0])


def bluebell():
    """Glowing berry bush that droops pale-blue bells."""
    m = Model('spore_bluebell', tex=32)
    stem, leaf = Mat(STEM, blob=0), Mat(LEAF, blob=0)
    bell = Mat(('#5a7fd8', '#6f94e8', '#86aaf4'), blob=0, overlays=[cover_top(('#b4ccff',), 1, 0, 1)])
    berry = Mat(('#8fe8ff', '#c4f6ff'), blob=0, glow=True)
    # age 0: sprout with two leaves
    b = stage(m, 0)
    m.cube(b, [-.5, 0, -.5], [1, 3, 1], stem)
    m.cube(b, [.5, 2, -.5], [2, .5, 1], leaf); m.cube(b, [-2.5, 1.5, -.5], [2, .5, 1], leaf)
    # age 1: taller stem, four leaves
    b = stage(m, 1)
    m.cube(b, [-.5, 0, -.5], [1, 6, 1], stem)
    for (o, s) in (([.5, 3, -.5], [3, .5, 1]), ([-3.5, 2, -.5], [3, .5, 1]), ([-.5, 4.5, .5], [1, .5, 3]), ([-.5, 3.5, -3.5], [1, .5, 3])):
        m.cube(b, o, s, leaf)
    # age 2: arching stems with closed buds
    b = stage(m, 2)
    m.cube(b, [-.5, 0, -.5], [1, 9, 1], stem)
    for sx in (-1, 1):
        m.cube(b, [sx * .5 - .5 + sx * 1, 8, -.5], [1, 1, 1], stem)
        m.cube(b, [sx * 2.5 - .5, 7, -.5], [1, 1, 1], stem)
        m.cube(b, [sx * 2.5 - .75, 5.5, -.75], [1.5, 1.5, 1.5], bell)
    for (o, s) in (([.5, 3, -.5], [3, .5, 1]), ([-3.5, 2, -.5], [3, .5, 1]), ([-.5, 4.5, .5], [1, .5, 3])):
        m.cube(b, o, s, leaf)
    # age 3: mature — three open bells, glowing berries
    b = stage(m, 3)
    m.cube(b, [-.5, 0, -.5], [1, 12, 1], stem)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1)):
        m.cube(b, [dx * 1.5 - .5, 11, dz * 1.5 - .5], [1 + abs(dx), 1, 1 + abs(dz)], stem)
        x, z = dx * 3.5, dz * 3.5
        m.cube(b, [x - .5, 9, z - .5], [1, 2, 1], stem)
        m.cube(b, [x - 1.5, 6.5, z - 1.5], [3, 2.5, 3], bell)
        m.cube(b, [x - 1, 6, z - 1], [2, .5, 2], bell)
        m.cube(b, [x - .5, 5.2, z - .5], [1, .8, 1], berry)
    for (o, s) in (([.5, 3, -.5], [4, .5, 1.5]), ([-4.5, 2, -.5], [4, .5, 1.5]), ([-.75, 4.5, .5], [1.5, .5, 4]), ([-.75, 3.5, -4.5], [1.5, .5, 4])):
        m.cube(b, o, s, leaf)
    m.glows(('#8fe8ff', '#c4f6ff'))
    return m


def bracken():
    """Spore fern: curled fiddleheads unrolling into wide fronds tipped with rust spores."""
    m = Model('spore_bracken', tex=32)
    stem = Mat(('#4a6a22', '#5a7e28'), blob=0)
    frond = Mat(('#3e7a24', '#4f8f2c', '#62a236', '#74b440'), blob=0, overlays=[spots(('#2f5e1a',), .1)])
    tip = Mat(('#a8642a', '#c27a34', '#d89040'), blob=0)
    curl = Mat(('#6aa63a', '#7eba46'), blob=0)

    def fern(b, h, reach, curl_tip=False):
        m.cube(b, [-.5, 0, -.5], [1, h * .6, 1], stem)
        for i, (dx, dz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
            if reach <= 0:
                continue
            ln = reach
            o = [-.5 if dx == 0 else (0 if dx > 0 else -ln), h * .6 - .5, -.5 if dz == 0 else (0 if dz > 0 else -ln)]
            s = [1.5 if dx == 0 else ln, .5, 1.5 if dz == 0 else ln]
            o[0] -= .25 if dx == 0 else 0; o[2] -= .25 if dz == 0 else 0
            m.cube(b, o, s, frond)
            # drooping outer half
            o2 = [(-.75 if dx == 0 else (ln - .2 if dx > 0 else -ln - ln * .45 + .2)), h * .6 - 1.5,
                  (-.75 if dz == 0 else (ln - .2 if dz > 0 else -ln - ln * .45 + .2))]
            s2 = [1.5 if dx == 0 else ln * .45, .5, 1.5 if dz == 0 else ln * .45]
            m.cube(b, o2, s2, frond)
            if curl_tip:
                m.cube(b, [o2[0] + (s2[0] - 1) * (dx > 0), h * .6 - 2.2, o2[2] + (s2[2] - 1) * (dz > 0)], [1, .7, 1], tip)
    b = stage(m, 0)
    m.cube(b, [-.5, 0, -.5], [1, 2, 1], stem)
    m.cube(b, [-.5, 2, -1], [1, 1, 2], curl); m.cube(b, [-.5, 2.5, .5], [1, 1, 1], curl)
    b = stage(m, 1)
    fern(b, 6, 2.5)
    m.cube(b, [-.5, 3.6, -1], [1, 1.5, 2], curl)
    b = stage(m, 2)
    fern(b, 10, 4.5)
    m.cube(b, [-.5, 6, -1], [1, 2, 2], curl)
    b = stage(m, 3)
    fern(b, 14, 5.4, curl_tip=True)  # stays inside the block footprint
    for (dx, dz) in ((1, 1), (-1, -1)):
        m.cube(b, [dx * 1.5 - .5, 0, dz * 1.5 - .5], [1, 6, 1], stem)
        m.cube(b, [dx * 1.5 - 1.5, 6, dz * 1.5 - .5], [3, .5, 1], frond)
    return m


def bogcap():
    """Marsh mushroom: a button that rises into a broad, spotted, drooping bog cap with small caps at its foot."""
    m = Model('spore_bogcap', tex=32)
    stem = Mat(('#c8bca0', '#d8ccb0', '#e6dcc4'), blob=0, overlays=[spots(('#a89c80',), .06)])
    cap = Mat(('#5e3a74', '#704888', '#84589c', '#9868ae'), blob=1, overlays=[spots(('#c8ecd0', '#a8e0c0'), .08)],
              down=Mat(('#c4b0d0', '#d0c0dc'), blob=0))
    gill = Mat(('#b8a4c8', '#c8b6d6'), blob=0)
    moss = Mat(('#4f7a2a', '#5f8f34', '#3f6a22'), blob=0)
    glowdot = Mat(('#a8f0c8', '#d0ffe0'), blob=0, glow=True)

    def shroom(b, x, z, h, r, cap_h=1.5, skirt=True):
        m.cube(b, [x - .75 if r < 4 else x - 1, 0, z - .75 if r < 4 else z - 1], [1.5 if r < 4 else 2, h, 1.5 if r < 4 else 2], stem)
        m.cube(b, [x - r / 2, h, z - r / 2], [r, cap_h, r], cap)
        if r >= 4:
            m.cube(b, [x - r / 2 + 1, h + cap_h, z - r / 2 + 1], [r - 2, 1, r - 2], cap)
            if skirt:  # drooping rim
                for dx, dz, sx, sz in ((-r / 2 - .5, -r / 2 + 1, .5, r - 2), (r / 2, -r / 2 + 1, .5, r - 2),
                                       (-r / 2 + 1, -r / 2 - .5, r - 2, .5), (-r / 2 + 1, r / 2, r - 2, .5)):
                    m.cube(b, [x + dx, h - 1, z + dz], [sx, 1.5, sz], cap)
            m.cube(b, [x - r / 2 + .5, h - .3, z - r / 2 + .5], [r - 1, .3, r - 1], gill)
    b = stage(m, 0)
    m.cube(b, [-2, 0, -2], [4, .5, 4], moss)
    shroom(b, 0, 0, 1.5, 2, 1)
    b = stage(m, 1)
    m.cube(b, [-2.5, 0, -2.5], [5, .5, 5], moss)
    shroom(b, 0, 0, 4, 3.5, 1.5)
    shroom(b, 2.5, 2, 1.5, 1.5, 1)
    b = stage(m, 2)
    m.cube(b, [-3, 0, -3], [6, .5, 6], moss)
    shroom(b, 0, 0, 7, 6, 2)
    shroom(b, 3, 2.5, 2.5, 2, 1)
    shroom(b, -3, -2, 1.5, 1.5, 1)
    b = stage(m, 3)
    m.cube(b, [-4, 0, -4], [8, .5, 8], moss)
    shroom(b, 0, 0, 10, 9, 2)
    shroom(b, 4.5, 3, 4, 3, 1.5)
    shroom(b, -4, -3.5, 2.5, 2.5, 1)
    shroom(b, -4.5, 3.5, 1.5, 1.5, 1)
    for (x, z) in ((2, -3), (-2.5, 2), (3.4, .5)):
        m.cube(b, [x - .25, 12.1, z - .25], [.5, .3, .5], glowdot)
    m.glows(('#a8f0c8', '#d0ffe0'))
    return m


PLANTS = {'spore_bluebell': bluebell, 'spore_bracken': bracken, 'spore_bogcap': bogcap}


def build(name):
    m = PLANTS[name]()
    m.key = name
    geo, img = m.build(seed=hash(name) % 1000 + 7)
    g = geo['minecraft:geometry'][0]
    size = g['description']['texture_width']
    out = []
    for bone in g['bones']:
        n = int(bone['name'][3:])
        stage_geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
            'description': {'identifier': f'geometry.{name}.age_{n}', 'texture_width': size, 'texture_height': size,
                            'visible_bounds_width': 2, 'visible_bounds_height': 2, 'visible_bounds_offset': [0, .5, 0]},
            'bones': [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': bone.get('cubes', [])}]}]}
        path = RP / f'models/blocks/{name}.age_{n}.geo.json'
        path.write_text(json.dumps(stage_geo, indent=1))
        out.append(path)
    # Blocks use alpha_test: keep glow pixels opaque (no emissive block material), unused atlas transparent.
    a = img.copy()
    px = a.load()
    for y in range(a.height):
        for x in range(a.width):
            r, gg, bb, al = px[x, y]
            if 0 < al < 255:
                px[x, y] = (r, gg, bb, 255)
    a.save(RP / f'textures/blocks/hybrids/{name}.png')
    return out, a.size


if __name__ == '__main__':
    for name in sys.argv[1:] or PLANTS:
        files, size = build(name)
        print(name, size, [f.name for f in files])
