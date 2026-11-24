"""Creeper designs 02-23 (Moss lives in designs.py)."""
import random
from forge import (_pick, Model, Mat, skeleton, cover_top, cover_bottom, veins, spots, rings, grain, stripe_band, creeper_face, pal,
                   cracks, glow_bottom)
from designs import design, flower, drips, cap, LEGS


# ------------------------------------------------------------------------------ more shared props
def spike(m, bone, x, y, z, h, base_mat, tip_mat=None, base=2, rot=None, pivot=None):
    """Tapered spike/stalagmite: wide base, narrow tip. Rigid when rotated (shared pivot)."""
    tip_mat = tip_mat or base_mat
    pv = pivot or [x, y, z]
    hb = max(1, round(h * .55))
    m.cube(bone, [x - base / 2, y, z - base / 2], [base, hb, base], base_mat, rot=rot, pivot=pv if rot else None)
    tb = max(1, base - 1)
    m.cube(bone, [x - tb / 2, y + hb, z - tb / 2], [tb, h - hb, tb], tip_mat, rot=rot, pivot=pv if rot else None)


def crystal(m, bone, x, y, z, w, h, mat, tip=None, rot=None):
    pv = [x, y, z]
    m.cube(bone, [x - w / 2, y, z - w / 2], [w, h, w], mat, rot=rot, pivot=pv if rot else None)
    tw = max(1, w - 1)
    m.cube(bone, [x - tw / 2, y + h, z - tw / 2], [tw, max(1, round(w * .9)), tw], tip or mat, rot=rot, pivot=pv if rot else None)


_LEAF_N = [0]


def leaf(m, bone, x, y, z, length, yaw, droop, mat, width=3, thick=.5, start=0):
    """A frond/petal radiating from (x,y,z): a child bone supplies the yaw, the cube supplies the droop."""
    _LEAF_N[0] += 1
    b = m.bone(f'{bone}_frond{_LEAF_N[0]}', [x, y, z], parent=bone, rotation=[0, yaw, 0])
    m.cube(b, [x + start, y, z - width / 2], [length, thick, width], mat, rot=[0, 0, -droop], pivot=[x, y, z])
    return b


_PF = [0]
FLOWER5 = [".P.P.",
           "PPPPP",
           ".PCP.",
           "PPPPP",
           ".P.P."]
FLOWER7 = ["...D...",
           "..DPD..",
           "DDPPPDD",
           "DPPCPPD",
           ".DPPPD.",
           ".DP.PD.",
           ".D...D."]


def flower_mask(n, petals=5, ring=.32, petal_r=.24, center_r=.16, rot=-90):
    """Pixel mask for an n x n five-petal blossom: P petal, D petal edge, C centre, . empty."""
    import math
    c = (n - 1) / 2
    pts = [(c + math.cos(math.radians(rot + k * 360 / petals)) * n * ring, c + math.sin(math.radians(rot + k * 360 / petals)) * n * ring)
           for k in range(petals)]
    rows = []
    for j in range(n):
        row = ''
        for i in range(n):
            dc = math.hypot(i - c, j - c)
            dp = min(math.hypot(i - px, j - py) for px, py in pts)
            if dc <= max(.6, n * center_r):
                row += 'C'
            elif dp <= n * petal_r:
                row += 'D' if dp > n * petal_r - .9 and n >= 7 else 'P'
            elif dc <= n * ring * .9:
                row += 'P'
            else:
                row += '.'
        rows.append(row)
    return rows


def pix_flower(m, parent, pos, petal, center, size=5, pitch=0, yaw=0, yaw_pivot=None, px=.75, thick=.5, edge=None, mask=None):
    """A crisp pixel-art blossom built as a flat plate of merged blocks (faces -z before rotation).
    pitch tilts it back toward facing up (90 = lying flat, facing the sky); yaw spins it about yaw_pivot."""
    _PF[0] += 1
    k = _PF[0]
    if yaw:
        parent = m.bone(f'pf{k}_yaw', yaw_pivot or pos, parent=parent, rotation=[0, yaw, 0])
    b = m.bone(f'pf{k}', pos, parent=parent, rotation=[pitch, 0, 0])
    rows = mask or (FLOWER7 if size >= 7 else FLOWER5)
    n = len(rows)
    c = (n - 1) / 2
    mats = {'P': petal, 'D': edge or petal, 'C': center}
    x0, y0, z0 = pos
    for j, row in enumerate(rows):
        i = 0
        while i < len(row):
            ch = row[i]
            if ch == '.':
                i += 1; continue
            r = i
            while r < len(row) and row[r] == ch:
                r += 1
            run = r - i
            zt = thick + (.35 if ch == 'C' else 0)
            m.cube(b, [x0 + (i - c - .5) * px, y0 + (c - j - .5) * px, z0 - zt / 2 - (.2 if ch == 'C' else 0)], [run * px, px, zt], mats[ch])
            i = r
    return b


def floaters(m, bone, pts, mat, s=1):
    for (x, y, z) in pts:
        m.cube(bone, [x - s / 2, y, z - s / 2], [s, s, s], mat)


# ================================================================================ 02 CAVE
@design('cave')
def cave():
    stone = ('#4c4b4d', '#5f5e60', '#747274', '#8a8887', '#a19f9b')
    ore = ('#e08a24', '#f7b23a', '#ffd76a')
    tan = Mat(('#b89c78', '#ccb28c', '#dcc6a2', '#e9d9ba'))
    tip = Mat(('#e6d6b6', '#f2e6cc'))
    head = Mat(stone, blob=0, overlays=[spots(ore, .05, 1, faces=('east', 'west', 'south', 'up')), creeper_face('#141416')])
    body = Mat(stone, blob=0, overlays=[spots(ore, .07, 1), veins(ore, .6, 5, branch=0)])
    leg = Mat(stone, blob=0, overlays=[spots(ore, .03)])
    m = skeleton(Model('cave'), head=head, body=body, legs=leg)
    m.glows(ore)
    spike(m, 'head', -2.5, 26, -2.5, 4, tan, tip)
    spike(m, 'head', 2.5, 26, -2, 3, tan, tip, base=2)
    spike(m, 'head', 1, 26, 2.5, 5, tan, tip)
    spike(m, 'head', -3, 26, 2.5, 2, tan, tip, base=1)
    oreb = Mat(ore)
    m.cube('head', [4, 20, -1], [0.6, 2, 2], oreb)
    m.cube('body', [-1, 11, -2.4], [2, 2, 0.5], oreb)
    m.cube('body', [1, 14, -2.4], [1, 1, 0.5], oreb)
    stal = Mat(('#7a7875', '#8f8d89', '#a7a49e'))
    drips(m, 'head', [0, 2, 0, 0, 0, 0, 3, 0], stal, -4, 4, 18.5, x_side=4, z0=-4, z1=4, out=0)
    for name, x, z in LEGS:
        spike(m, name, x - .5, 6, z + (.8 if z > 0 else -.8), 4 if name in ('leg2', 'leg1') else 3, tan, tip, base=2)
    return m, {'seed': 202, 'alt': ((.9, .9, .95), (0, 0, 0))}


# ================================================================================ 03 CRYSTAL
# (crystal: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 04 SWAMP
# (swamp: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 05 DESERT
@design('desert')
def desert():
    sand = ('#c4a576', '#d2b688', '#dec59a', '#e8d4ad', '#f1e2c2')
    rope_c = ('#7d4f26', '#94602f', '#a8733c')
    rope = Mat(rope_c, blob=0)
    head = Mat(sand, blob=0, overlays=[creeper_face('#5b3a22', '#4a2c18')])
    body = Mat(sand, blob=0)
    leg = Mat(sand, blob=0)
    m = skeleton(Model('desert'), head=head, body=body, legs=leg)
    sides = ('north', 'south', 'east', 'west', 'up')
    m.cube('body', [-4.4, 14, -2.4], [8.8, 1, 4.8], rope, rot=[0, 0, 8], pivot=[0, 14.5, 0], faces=sides)
    m.cube('body', [-4.4, 9, -2.4], [8.8, 1, 4.8], rope, rot=[0, 0, -10], pivot=[0, 9.5, 0], faces=sides)
    m.cube('head', [-4.4, 19, -4.4], [8.8, 1, 8.8], rope, rot=[0, 0, -6], pivot=[0, 19.5, 0], faces=sides)
    m.cube('head', [4.1, 15, 2], [.6, 4, .6], rope)
    cac = Mat(('#3f7a32', '#4f8f3a', '#5fa244', '#6fb24e'), blob=0, overlays=[spots(('#e6e0b8',), .08)])
    m.cube('head', [0, 26, 0], [3.5, 5, 3.5], cac)
    m.cube('head', [3.5, 27, 1], [1.5, 1, 1.5], cac)
    m.cube('head', [4, 28, 1], [1, 2, 1.5], cac)
    pink, pinkd = Mat(('#e95f8f', '#f582a8')), Mat(('#ffc0d4', '#ffd8e4'))
    m.cube('head', [.5, 31, .5], [2.5, 1, 2.5], pink)
    m.cube('head', [1.25, 31.5, 1.25], [1, 1.2, 1], pinkd)
    m.cube('head', [-3, 26, -2], [1, 2, 1], Mat(('#e8d8b8', '#f4e8d0')))
    twig = Mat(('#7a4a26', '#8d5a30', '#6a3e1e'))
    m.cube('leg2', [-5, 3, -5.5], [1, 6, 1], twig, rot=[0, 0, 15], pivot=[-4.5, 3, -5])
    m.cube('leg2', [-7, 7, -5.5], [3, 1, 1], twig, rot=[0, 0, -30], pivot=[-4.5, 7, -5])
    m.cube('leg2', [-5, 8, -5.5], [1, 3, 1], twig, rot=[0, 0, 35], pivot=[-4.5, 8, -5])
    m.cube('leg2', [-6.5, 9.5, -5.5], [1, 2, 1], twig, rot=[0, 0, 40], pivot=[-6, 9.5, -5])
    return m, {'seed': 505}


# ================================================================================ 06 SNOW
@design('snow')
def snow():
    ice = ('#7fa9d6', '#94bae2', '#a9caec', '#bfd9f4', '#d6e8fa')
    white = ('#dfe9f3', '#eef4fa', '#ffffff')
    sn = Mat(white, blob=1)
    icicle = Mat(('#bfe0ff', '#d8eeff', '#ffffff'))
    head = Mat(ice, blob=0, overlays=[cover_top(white, 1, .6, 2), creeper_face('#26405f')])
    body = Mat(ice, blob=0)
    leg = Mat(ice, blob=0, overlays=[cover_top(white, 1, .6, 2)])
    m = skeleton(Model('snow'), head=head, body=body, legs=leg)
    m.cube('head', [-4.5, 26, -4.5], [9, 2, 9], sn)
    drips(m, 'head', [1, 2, 0, 1, 0, 2, 1, 1], sn, -4, 4, 26, z_front=-4)
    drips(m, 'head', [2, 1, 1, 0, 2, 1, 0, 2], sn, -4, 4, 26, x_side=4, z0=-4, z1=4)
    drips(m, 'head', [1, 0, 2, 1, 1, 0, 1, 2], sn, -4, 4, 26, x_side=-4, z0=-4, z1=4)
    for x, z, h in ((-3.5, -4.6, 3), (2.5, -4.6, 2), (3.9, -2, 5), (3.9, 1.5, 3), (-4.9, 2.5, 4), (-1, -4.6, 1)):
        m.cube('head', [x, 24 - h, z], [1, h, 1], icicle)
    tip = Mat(('#a9d0f5', '#cfe6ff', '#eef8ff'))
    crystal(m, 'head', 1.5, 28, 0, 3, 3, tip, tip)
    crystal(m, 'head', -2.5, 28, -2, 2, 2, tip, tip)
    m.cube('body', [3.9, 13, -1], [1, 3, 1], icicle)
    for name, x, z in LEGS:
        m.cube(name, [x - 2.5, 6, z - 2.5], [5, 1.5, 5], sn)
        m.cube(name, [x - 2.5, 4.5, z - 2.6], [2, 1.5, .4], sn)
    return m, {'seed': 606, 'alt': ((.95, .97, 1.0), (0, 0, 0))}


# ================================================================================ 07 JUNGLE
# (jungle: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 08 MUSHROOM
@design('mushroom')
def mushroom():
    stem = ('#d6cbbb', '#e2d8c9', '#ece4d7', '#f5efe6')
    red = ('#a81e24', '#bf2a2c', '#d23934', '#e04a40')
    dots = ('#f3ece2', '#fffaf2')
    capm = Mat(red, blob=1, overlays=[spots(dots, .06, 2, faces=('up', 'north', 'south', 'east', 'west'))], down=Mat(('#d9c4ae', '#e6d4c0', '#c9b29c')))
    head = Mat(stem, blob=0, overlays=[creeper_face('#3a2a26')])
    body = Mat(stem, blob=0, overlays=[spots(('#c0392f', '#d65a4a'), .04)])
    leg = Mat(stem, blob=0, overlays=[cover_bottom(('#8a7a68', '#9e8c78'), 1, .5)])
    m = skeleton(Model('mushroom'), head=head, body=body, legs=leg)
    m.cube('head', [-7, 23.5, -7], [14, 3, 14], capm)
    m.cube('head', [-5.5, 26.5, -5.5], [11, 2, 11], capm)
    m.cube('head', [-3.5, 28.5, -3.5], [7, 1, 7], capm)
    small = Mat(red, overlays=[spots(dots, .12, 1)], down=Mat(('#e6d4c0',)))
    sstem = Mat(('#e8dfd0', '#f4eee4'))
    # The little mushrooms at its feet are now a trail it leaves behind (particles/cs_trail_mushroom).
    m.cube('body', [4, 12, -.5], [2, 1, 1], sstem)
    m.cube('body', [4.8, 12.5, -.5], [1, 2, 1], sstem)
    m.cube('body', [4.0, 14.5, -1.25], [2.5, 1.2, 2.5], small)
    return m, {'seed': 808, 'bounds': (4, 5, 1.6)}


# ================================================================================ 09 SCULK
@design('sculk')
def sculk():
    deep = ('#0b1820', '#11222c', '#172d38', '#1e3a46', '#264654')
    core = ('#7ff6ee', '#c0fffa')
    halo = ('#14a8a8', '#1fc4c0', '#2ee0d8')
    cm = Mat(('#1fbfbe', '#36dcd6', '#6ff4ec'), blob=0, glow=True)
    head = Mat(deep, blob=1, overlays=[cracks(core, halo, .8, drift=.5), creeper_face('#03070a')])
    body = Mat(deep, blob=1, overlays=[cracks(core, halo, 1.3, drift=.5, branch=.25)])
    leg = Mat(deep, blob=1, overlays=[cracks(core, halo, .8, drift=.5)])
    m = skeleton(Model('sculk'), head=head, body=body, legs=leg)
    m.glows(core, halo)
    for x, z, h, cx in ((-2.5, -1, 4, -1), (2.5, -1, 5, 1), (-.5, 2.5, 3, -1), (3.5, 2.5, 3, 1)):
        m.cube('head', [x - .5, 26, z - .5], [1, h, 1], cm)
        m.cube('head', [x - .5 + cx, 26 + h - 1, z - .5], [1, 1, 1], cm)
        m.cube('head', [x - .5 + cx * 2, 26 + h - 2, z - .5], [1, 1, 1], cm)
    for name, x, z in LEGS:
        m.cube(name, [x + (1 if x > 0 else -2), 6, z - .5], [1, 2 + (name == 'leg3'), 1], cm)
    m.cube('body', [3.5, 15, 0], [1, 3, 1], cm)
    m.cube('body', [4.5, 17, 0], [1, 1, 1], cm)
    floaters(m, 'body', [(-6, 14, -2), (6, 9, -3), (-5.5, 20, 2), (6.5, 22, -1), (-7, 5, 0), (5, 3, -6), (2, 28, -5)], Mat(core, glow=True), .8)
    return m, {'seed': 909, 'alt': ((.85, .95, 1.0), (0, 0, 0))}


# ================================================================================ 10 NETHER
@design('nether')
def nether():
    rack = ('#4e2026', '#5e282e', '#6e3036', '#7e3a3e', '#8e4446')
    core = ('#ffc240', '#ffe07a')
    halo = ('#d84a10', '#ff6a10', '#ff8a1e')
    coral = Mat(('#9a1a2a', '#b82434', '#d23446', '#e8505e'), blob=0)
    head = Mat(rack, blob=1, overlays=[cracks(core, halo, .7), creeper_face('#170709')])
    body = Mat(rack, blob=1, overlays=[cracks(core, halo, 1.1, branch=.2)])
    leg = Mat(rack, blob=1, overlays=[cracks(core, halo, .6), glow_bottom(halo, 1)])
    m = skeleton(Model('nether'), head=head, body=body, legs=leg)
    m.glows(core, halo, ('#ff8f1e', '#ffb43a', '#ffd870'))

    def branchy(bone, x, y, z, h, side):
        m.cube(bone, [x - .5, y, z - .5], [1, h, 1], coral)
        m.cube(bone, [x - .5 + side, y + h - 2, z - .5], [1, 1, 1], coral)
        m.cube(bone, [x - .5 + side, y + h - 1, z - .5], [1, 2, 1], coral)
    branchy('head', -3, 26, -2, 4, -1); branchy('head', 2, 26, -3, 3, 1); branchy('head', 3, 26, 2, 5, 1)
    branchy('head', -1, 26, 3, 3, -1); branchy('head', 0, 26, 0, 2, 1); branchy('head', 3.5, 24, -3.5, 3, 1)
    branchy('leg3', 3, 6, -6, 4, 1); branchy('leg1', 3.5, 6, 5, 3, -1); branchy('body', 3.5, 14, 1, 3, 1)
    floaters(m, 'body', [(-6, 12, -3), (5.5, 7, -4), (-5, 18, 1), (6, 19, -2), (-3, 3, -7), (6.5, 26, 0)], Mat(('#ff8f1e', '#ffb43a', '#ffd870')), .7)
    return m, {'seed': 1010}


# ================================================================================ 11 END
@design('end')
def end():
    es = ('#cbc492', '#d8d1a2', '#e4ddb2', '#eee8c4', '#bdb67f')
    core = ('#c47af0', '#dca4fc')
    halo = ('#7d2fb3', '#9440c8')
    pm = Mat(('#7d2fb3', '#9a45cf', '#b766e6'), blob=0, glow=True)
    head = Mat(es, blob=1, overlays=[cracks(core, halo, .6), creeper_face('#2d0f45', '#3c1a5a')])
    body = Mat(es, blob=1, overlays=[cracks(core, halo, 1.0, branch=.2)])
    leg = Mat(es, blob=1, overlays=[cracks(core, halo, .5)])
    m = skeleton(Model('end'), head=head, body=body, legs=leg)
    m.glows(core)
    for sx in (-1, 1):
        x = 2.5 * sx
        m.cube('head', [x - .5, 26, -.5], [1, 4, 1], pm)
        m.cube('head', [x - .5, 29, .5], [1, 1, 2], pm)
        m.cube('head', [x - .5, 30, 2], [1, 2, 1], pm)
    m.cube('head', [-.5, 26, 2.5], [1, 2, 1], pm)
    floaters(m, 'body', [(-6.5, 14, -2), (6, 10, -3), (-6, 21, 1), (6.5, 24, -1), (-5, 4, -5), (4.5, 2, -7), (0, 31, -4), (7, 17, 2)], Mat(core, glow=True), 1)
    return m, {'seed': 1111}


# ================================================================================ 12 WATER
def water_wash(water, crest, foam, y0, slope=0.0, amp=1.0, faces=('north', 'south', 'east', 'west'), drops=0, band=2, second=0):
    """Water rising up a face: everything below a wavy line turns to water, with a bright crest
    and a foam highlight riding on top of it. y0 is the waterline as a fraction of the face height."""
    import numpy as np
    from forge import quantize, smooth_noise, _bayer
    wp, cp, fp = pal(*water), pal(*crest), pal(*foam)
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face == 'down':
            img[:] = quantize(np.clip(smooth_noise(rng, w, h, 1), 0, .999), wp); return
        if face not in faces:
            return
        sl = slope if face in ('north', 'east') else -slope
        n = quantize(np.clip(smooth_noise(rng, w, h, 2) + (_bayer(w, h) - .5) * .15, 0, .999), wp)
        for x in range(w):
            line = int(round(y0 * h + sl * (x - w / 2) + amp * np.sin(x * 1.1 + (3 if face in ('south', 'west') else 0))))
            for y in range(max(0, line), h):
                img[y, x] = n[y, x]
            # the stream: a bright band with a foam edge on top and a deeper shadow under it
            for t in range(band):
                if 0 <= line + t < h:
                    img[line + t, x] = cp[(x + t) % len(cp)]
            if 0 <= line < h and x % 3 == 0:
                img[line, x] = fp[0]
            if 0 <= line + band < h:
                img[line + band, x] = wp[0]
            if second and 0 <= line + band + second < h and (x + line) % 5 != 0:
                img[line + band + second, x] = cp[0]
        for _ in range(drops):  # a few droplets clinging above the water
            x, y = rng.integers(w), rng.integers(max(1, int(y0 * h) - 1))
            img[y, x] = fp[0]
            if y + 1 < h:
                img[y + 1, x] = cp[0]
    return f


def lily_texture(top, groove, edge, cx, cz, r):
    """Radial grooves and a darker rim, computed in model space so every strip of the pad lines up."""
    import math
    gp, ep = pal(*groove), pal(*edge)
    def f(img, face, rng, info):
        if face != 'up':
            return
        h, w, _ = img.shape
        x0, z0 = info['cell']
        for j in range(h):
            for i in range(w):
                px, pz = x0 + i + .5, z0 + j + .5
                d = math.hypot(px - cx, pz - cz)
                a = math.degrees(math.atan2(pz - cz, px - cx)) % 45
                if d > r - 1.1:
                    img[j, i] = ep[rng.integers(len(ep))]
                elif d > 1.2 and (a < 5 or a > 40):
                    img[j, i] = gp[rng.integers(len(gp))]
    return f


@design('water')
def water():
    """Water Creeper, redrawn from the lily-pad reference: a bright green creeper wading in water.
    The water climbs its legs and washes diagonally across the body, a big notched lily pad sits on its
    head with a pink water lily, and bubbles (particles) pop around it while lily pads trail behind."""
    import math
    green = ('#2e9450', '#38a65a', '#45b862', '#56c86c', '#6ad676')
    water_c = ('#1c8ea8', '#24a0ba', '#2eb2ca', '#3ac2d6')
    crest = ('#4ee4fa', '#66eeff', '#58e8fc')
    foam = ('#c8fbff', '#e6ffff')
    face = creeper_face('#0b130c')
    head = Mat(green, blob=1, overlays=[water_wash(('#2f9e86', '#36aa90', '#3db49a'), ('#48c8b0',), ('#7ee8d4',), .78, slope=-.3,
                                                   amp=.4, faces=('east',), band=1), face])
    body = Mat(green, blob=1, overlays=[water_wash(('#22a0ba', '#2aacc4', '#30b4ca'), crest, foam, .4, slope=-.55, amp=0,
                                                   drops=1, band=2, second=3)])
    leg = Mat(green, blob=1, overlays=[water_wash(water_c, crest, foam, .55, slope=0, amp=.4, band=1)])
    m = skeleton(Model('water'), head=head, body=body, legs=leg)
    m.glows(crest)  # the stream shimmers faintly in the dark, like the reference

    # ---- the lily pad hat: a round, notched pad bigger than the head, tipped slightly to one side
    pad_bone = m.bone('lily_pad', [0, 26, 0], parent='head', rotation=[-4, 0, 3])
    R, cx, cz = 6.9, 0.0, 0.0
    top = ('#479e1c', '#52ac22', '#5eb82a')
    pad_mat = Mat(top, blob=1.5, overlays=[lily_texture(top, ('#70c23a', '#7ccc44'), ('#2c6a10', '#327412'), cx, cz, R)],
                  sides=Mat(('#2a6410', '#2f6e12')), down=Mat(('#265a0e', '#2a6410')))
    notch = 270 + 18  # front (-z), a little right of centre, like the reference
    for zi in range(-8, 8):
        row = []
        for xi in range(-8, 8):
            px, pz = xi + .5, zi + .5
            d = math.hypot(px - cx, pz - cz)
            ang = math.degrees(math.atan2(pz, px)) % 360
            inside = d <= R and not (d > 1.0 and abs((ang - notch + 180) % 360 - 180) < 11)
            row.append(inside)
        x = -8
        while x < 8:
            if not row[x + 8]:
                x += 1; continue
            r = x
            while r < 8 and row[r + 8]:
                r += 1
            m.cube(pad_bone, [x, 26, zi], [r - x, 1.4, 1], pad_mat, cell=(x, zi))
            x = r
    # ---- pink water lily at the back-right of the pad: two layers of crisp pixel petals and a gold heart
    pink, pale, gold = Mat(('#ffa2c8', '#ffb4d2'), blob=0), Mat(('#ffd2e4', '#ffe0ec'), blob=0), Mat(('#ffc83a', '#ffd85a'), blob=0)
    fx, fz = 2.8, 2.4
    lily = m.bone('lily_flower', [fx, 27.4, fz], parent=pad_bone)
    y0 = 27.4
    m.cube(lily, [fx - .8, y0 + .7, fz - .8], [1.6, 1.4, 1.6], gold)
    for dx, dz in ((1.7, 0), (-1.7, 0), (0, 1.7), (0, -1.7)):   # four chunky pink petals, tipped outward
        m.cube(lily, [fx + dx - .95, y0, fz + dz - .95], [1.9, 1.6, 1.9], pink,
               rot=[18 * (dz > 0) - 18 * (dz < 0), 0, -18 * (dx > 0) + 18 * (dx < 0)], pivot=[fx, y0, fz])
    for dx, dz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):               # paler petals between them
        m.cube(lily, [fx + dx * 1.3 - .65, y0, fz + dz * 1.3 - .65], [1.3, 1.1, 1.3], pale)
    # Bubbles pop in around it and lily pads trail behind it as particles (tools/trails.py).
    return m, {'seed': 1212, 'alt': ((.9, .95, 1.0), (0, 0, 0))}


# ================================================================================ 13 LAVA
def lava_seams(core, halo, min_block=2, max_block=4, coverage=1.0, keep_clear=None, faces=('north', 'south', 'east', 'west', 'up')):
    """Rock broken into irregular rectangular blocks, with molten lava glowing in the 1-px seams between them.
    The face is split again and again (random horizontal/vertical cuts, each with a one-pixel jog) until the
    blocks are min..max pixels; each cut becomes a bright core line with a dimmer orange edge on the rock.
    coverage < 1 leaves some cuts dark; keep_clear: (x0, y0, x1, y1) fractions kept as plain rock on the front."""
    import numpy as np
    cp, hp = pal(*core), pal(*halo)
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces:
            return
        seam = np.zeros((h, w), bool)
        stack = [(0, 0, w, h)]
        while stack:
            x0, y0, x1, y1 = stack.pop()
            bw, bh = x1 - x0, y1 - y0
            if max(bw, bh) <= max_block and (rng.random() < .5 or max(bw, bh) <= min_block + 1):
                continue
            if bw < 2 * min_block + 1 and bh < 2 * min_block + 1:
                continue
            vertical = bw > bh if abs(bw - bh) > 1 else rng.random() < .5
            if vertical and bw >= 2 * min_block + 1:
                c = int(rng.integers(x0 + min_block, x1 - min_block))
                jog = int(rng.integers(y0, y1))
                on = rng.random() < coverage
                for y in range(y0, y1):
                    cx = c + (1 if y >= jog and c + 1 < x1 - 1 else 0)
                    if on:
                        seam[y, cx] = True
                stack += [(x0, y0, c, y1), (c + 1, y0, x1, y1)]
            elif bh >= 2 * min_block + 1:
                c = int(rng.integers(y0 + min_block, y1 - min_block))
                jog = int(rng.integers(x0, x1))
                on = rng.random() < coverage
                for x in range(x0, x1):
                    cy = c + (1 if x >= jog and c + 1 < y1 - 1 else 0)
                    if on:
                        seam[cy, x] = True
                stack += [(x0, y0, x1, c), (x0, c + 1, x1, y1)]
        if keep_clear and face == 'north':
            x0, y0, x1, y1 = keep_clear
            seam[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = False
        edge = np.zeros_like(seam)
        edge[1:] |= seam[:-1]; edge[:-1] |= seam[1:]; edge[:, 1:] |= seam[:, :-1]; edge[:, :-1] |= seam[:, 1:]
        edge &= ~seam
        for y, x in zip(*np.nonzero(edge)):
            if rng.random() < .55:
                img[y, x] = hp[rng.integers(len(hp))]
        for y, x in zip(*np.nonzero(seam)):
            img[y, x] = cp[rng.integers(len(cp))]
    return f


def molten_feet(core, halo, rock_rows=3, faces=('north', 'south', 'east', 'west')):
    """Feet standing in their own glow: the lower part of each foot is molten, with a few rock chunks left in it."""
    cp, hp = pal(*core), pal(*halo)
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face == 'down':
            for y in range(h):
                for x in range(w):
                    img[y, x] = cp[rng.integers(len(cp))]
            return
        if face not in faces:
            return
        for y in range(min(rock_rows, h), h):
            for x in range(w):
                r = rng.random()
                if y == rock_rows and r < .4:
                    continue  # ragged top edge: some rock pixels stay
                img[y, x] = hp[rng.integers(len(hp))] if (y < h - 1 and r < .7) else cp[rng.integers(len(cp))]
    return f


# (lava: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 14 FLOWER
@design('flower')
def flower_creeper():
    green = ('#4f7a2a', '#618f32', '#73a23a', '#86b444', '#99c24e')
    blush = ('#b98a7c', '#cf9a8c', '#d8a8a0')
    lm = Mat(green[1:], blob=0)
    leafm = Mat(('#4a8228', '#5c9830', '#70ac3a'), blob=0)
    head = Mat(green, blob=1, blotch=(blush, .8, 1), overlays=[creeper_face('#1b2a12')])
    body = Mat(green, blob=1, blotch=(blush, .76, 1), overlays=[veins(green[2:], .6, 6)])
    leg = Mat(green, blob=1, blotch=(blush, .74, 1))
    m = skeleton(Model('flower'), head=head, body=body, legs=leg)
    pink, pinkd = Mat(('#ea7fae', '#f08fb8', '#f49cc2'), blob=0), Mat(('#cf5f97', '#c4568c'), blob=0)
    pinkl, pinkld = Mat(('#f7b8d2', '#fcc8dc'), blob=0), Mat(('#e698ba',), blob=0)
    white, whited = Mat(('#f3efe7', '#fffdf8'), blob=0), Mat(('#d8d2c6', '#e2dcd0'), blob=0)
    gold = Mat(('#f2b42a', '#ffd24a'), blob=0)
    m.cube('head', [-4.5, 26, -4.5], [9, 1.5, 9], lm)
    for x, z in ((-4.2, -4.2), (2.6, -4.4), (4.2, 1), (-1, 4.2), (-4.4, 1.5), (3, 3.5)):
        m.cube('head', [x - 1, 24.5, z - 1], [2, 2.5, 2], leafm)
    # wreath: blossoms ringing the crown, tipped outward
    for yaw, (petal, edge), sz in ((-40, (white, whited), 5), (40, (pinkl, pinkld), 5), (90, (pinkl, pinkld), 7), (135, (white, whited), 5),
                                   (180, (pink, pinkd), 7), (225, (white, whited), 5), (270, (pink, pinkd), 7), (315, (white, whited), 5)):
        pix_flower(m, 'head', (0, 27.8, -3.9), petal, gold, size=sz, pitch=50, yaw=yaw, yaw_pivot=(0, 27.6, 0),
                   px=.8 if sz == 7 else .65, edge=edge)
    pix_flower(m, 'head', (-1.2, 27.6, .6), white, gold, 5, pitch=88, px=.7)
    pix_flower(m, 'head', (1.6, 27.8, 1.4), pinkl, gold, 5, pitch=80, px=.7)
    # the big feature bloom over the front-right corner
    pix_flower(m, 'head', (3.9, 28, -3.9), pink, gold, 7, pitch=45, px=.95, edge=pinkd, yaw=-40, yaw_pivot=(3.9, 28, -3.9))
    # blossoms climbing the body
    pix_flower(m, 'body', (1.4, 13, -2.25), pink, gold, 7, px=.6, edge=pinkd)
    pix_flower(m, 'body', (-2, 8.6, -2.25), pinkl, gold, 5, px=.6)
    pix_flower(m, 'body', (2.2, 17, 2.25), white, gold, 5, px=.6, yaw=180, yaw_pivot=(2.2, 17, 0))
    m.cube('body', [-.5, 6, -2.3], [1, 5, .4], leafm)
    m.cube('body', [-1.5, 9.5, -2.3], [3, .8, .4], leafm)
    # feet: blooms and leaves
    pix_flower(m, 'leg2', (-3, 6.6, -5.4), white, gold, 7, pitch=55, px=.8, edge=whited)
    pix_flower(m, 'leg3', (3, 6.8, -5), pinkl, gold, 5, pitch=62, px=.7)
    pix_flower(m, 'leg1', (3.4, 6.6, 3.6), pink, gold, 7, pitch=70, px=.8, edge=pinkd)
    pix_flower(m, 'leg0', (-3.5, 4.5, 6.2), white, gold, 5, pitch=20, px=.6, yaw=180, yaw_pivot=(-3.5, 4.5, 4))
    for name, x, z in LEGS:
        m.cube(name, [x - 2.2, 5.6, z - 2.2], [4.4, .8, 4.4], lm)
    return m, {'seed': 1414}


# ================================================================================ 15 THORN
def thorn_cone(m, bone, x, y, z, rot, size=1.0, mats=None):
    """A slender tapered thorn: tan base, pale body, cream point. Built pointing up, then tipped by rot."""
    base, mid, tip = mats
    k = size
    pv = [x, y, z]
    m.cube(bone, [x - .9 * k, y, z - .9 * k], [1.8 * k, 1.2 * k, 1.8 * k], base, rot=rot, pivot=pv)
    m.cube(bone, [x - .6 * k, y + 1.2 * k, z - .6 * k], [1.2 * k, 1.5 * k, 1.2 * k], mid, rot=rot, pivot=pv)
    m.cube(bone, [x - .3 * k, y + 2.7 * k, z - .3 * k], [.6 * k, 1.4 * k, .6 * k], tip, rot=rot, pivot=pv)


def draped_vines(green, brown, count=3, faces=('north', 'south', 'east', 'west')):
    """Vines draped over a face: wandering 1-px strands that run mostly downward, green with brown runners."""
    gp, bp = pal(*green), pal(*brown)
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces:
            return
        for i in range(count):
            col = bp if i % 3 == 2 else gp
            x = int(rng.integers(w))
            for y in range(0, int(rng.integers(h // 2, h))):
                if info.get('face') and face == 'north' and 1 <= x <= w - 2 and h * .2 < y < h * .9:
                    break  # keep the creeper face readable
                img[y, x % w] = col[rng.integers(len(col))]
                if rng.random() < .35:
                    x += 1 if rng.random() < .5 else -1
                    x = max(0, min(w - 1, x))
                    img[y, x] = col[rng.integers(len(col))]
    return f


# (thorn: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 16 PHANTOM
@design('phantom')
def phantom():
    pale = ('#9fb0a8', '#b4c4bc', '#c8d6cf', '#dbe6e0', '#a49cbc')
    wing_c = ('#5e5680', '#6c6488', '#7f77a0', '#958db6', '#aca5c9')
    wm = Mat(wing_c, blob=1, overlays=[cover_top(('#b8b2d4', '#c8c2e0'), 1, .3, 1), cover_bottom(('#4c4566', '#423c5a'), 1, .7)])
    head = Mat(pale, blob=1, overlays=[cover_top(('#9a92b8', '#aaa2c6'), 1, .3, 1), creeper_face('#1a2230')])
    body = Mat(pale, blob=1, blotch=(('#8f86ae', '#a39bc0'), .8, 1))
    leg = Mat(pale, blob=1, overlays=[cover_bottom(('#7a7298', '#6a6288'), 2, .6)])
    m = skeleton(Model('phantom'), head=head, body=body, legs=leg)
    # two ragged membrane wings per side: a spar with tattered strips hanging from it, swept back and down
    for (ry, rz, top, lens) in ((12, -22, 17, (6, 8, 5, 9, 4, 7, 3, 6, 2)), (28, -40, 15, (5, 7, 4, 6, 3, 5, 2))):
        for i, ln in enumerate(lens):
            m.sym('body', [4 + i, top - ln, 1.2], [1, ln, .5], wm, rot=[0, ry, rz], pivot=[4, top, 1.5])
        m.sym('body', [4, top, 1.2], [len(lens) + .5, 1, .6], wm, rot=[0, ry, rz], pivot=[4, top, 1.5])
    # wispy tendrils curling off the crown
    wisp = Mat(wing_c[2:])
    for x, z, seq in ((-3, 1, ((0, 2), (-1, 1), (-2, 1))), (2, 2, ((0, 3), (1, 1), (2, 2)))):
        y = 26
        for dx, h in seq:
            m.cube('head', [x + dx, y, z], [1, h, 1], wisp)
            y += h
    return m, {'seed': 1616, 'bounds': (5, 5, 1.6)}


# ================================================================================ 17 GIANT
@design('giant')
def giant():
    green = ('#5c9a2c', '#74b236', '#8cc640', '#a2d64c')
    beige = ('#b9b6a0', '#cbc8b2', '#ddd9c6')
    lime = ('#a8cf36', '#bde040', '#cfee56')
    lm = Mat(lime, blob=0)
    head = Mat(green, blob=0, blotch=(beige, .64, 0), overlays=[cover_top(lime, 1, .5, 3), creeper_face('#16220f', '#1d2a14')])
    body = Mat(green, blob=0, blotch=(beige, .62, 0))
    leg = Mat(green, blob=0, blotch=(beige, .62, 0), overlays=[cover_top(lime, 1, .5, 1), cover_bottom(('#4c4c3e', '#5c5c4a'), 1, .7)])
    m = skeleton(Model('giant'), head=head, body=body, legs=leg)
    m.cube('head', [-4.3, 26, -4.3], [8.6, .8, 8.6], lm)
    drips(m, 'head', [0, 0, 0, 0, 0, 2, 4, 3], lm, -4, 4, 26, x_side=4, z0=-4, z1=4)
    drips(m, 'head', [2, 0, 0, 0, 0, 1, 2, 3], lm, -4, 4, 26, z_front=-4)
    for name, x, z in LEGS:
        m.cube(name, [x - 2.2, 5.6, z - 2.2], [4.4, .8, 4.4], lm)
    return m, {'seed': 1717}


# ================================================================================ 18 MINIATURE
@design('miniature')
def miniature():
    green = ('#4c9a2c', '#5eb034', '#74c43c', '#8ad44a', '#a2e05a')
    head = Mat(green, blob=0, overlays=[creeper_face('#0f1a0c')])
    body = Mat(green, blob=0)
    leg = Mat(green, blob=0, overlays=[cover_bottom(('#3a5a26', '#2e4a1e'), 1, .6)])
    m = skeleton(Model('miniature'), head=head, body=body, legs=leg)
    return m, {'seed': 1818}


# ================================================================================ 19 GLOWING
@design('glowing')
def glowing():
    deep = ('#1f6a1a', '#287e20', '#329428', '#3ea830')
    neon = ('#6edc42', '#8cec58', '#b0f87a', '#d4ff8c')
    bright = ('#d4ff8c', '#eaffb8')
    head = Mat(deep, blob=0, blotch=(neon, .6, 1), overlays=[spots(bright, .05, 1), creeper_face('#0c2a08', '#123a0e')])
    body = Mat(deep, blob=0, blotch=(neon, .58, 1), overlays=[spots(bright, .06, 1)])
    leg = Mat(deep, blob=0, blotch=(neon, .55, 1), overlays=[spots(bright, .05, 1)])
    m = skeleton(Model('glowing'), head=head, body=body, legs=leg)
    m.glows(neon, bright)
    # The floating glow cubes are now a trail of glowing motes (particles/cs_trail_glowing).
    return m, {'seed': 1919}


# ================================================================================ 20 SPORE QUEEN
# (spore_queen: design moved to designs_redo.py on 2026-11-23; the previous version is kept in designs_previous_0_8_31.py)
# ================================================================================ 21 GRASS CROWN
SKULL8 = [
    "BBBBBBBB",
    "BBBBBBBB",
    "BEEBBEEB",
    "BEEBBEEB",
    "BBBNNBBB",
    "BBBBBBBB",
    "BTBTBTBB",
    ".BBBBBB.",
]


def skull_face(bone_c):
    bonep = pal(*bone_c); dark = pal('#5a3a22')[0]; nose = pal('#7a5034')[0]; teeth = pal('#c8bca0')[0]

    def f(img, face, rng, info):
        if face != 'north' or not info.get('face'):
            return
        for py, row in enumerate(SKULL8):
            for px, ch in enumerate(row):
                if ch != '.':
                    img[py, px] = {'B': bonep[(px * 7 + py * 3) % len(bonep)], 'E': dark, 'N': nose, 'T': teeth}[ch]
    return f


@design('grass_crown')
def grass_crown():
    leafc = ('#355a1e', '#426e24', '#52822c', '#649636', '#78a842')
    grass = ('#5c8e2a', '#72a634', '#8cbc40', '#a6d04e')
    bone_c = ('#e6dcc4', '#efe6d0', '#d8ccb0')
    head = Mat(leafc, blob=1, overlays=[skull_face(bone_c)])
    body = Mat(leafc, blob=1, overlays=[spots(grass, .06)])
    leg = Mat(leafc, blob=1)
    m = skeleton(Model('grass_crown'), head=head, body=body, legs=leg)
    brim = Mat(('#2c4a16', '#365a1c', '#406a22'), blob=0)
    m.cube('head', [-6, 25.5, -6], [12, 1, 12], brim)
    gm = Mat(grass, blob=0)
    tips = Mat(('#b4d858', '#c8e46a'))
    r = random.Random(21)
    for x in range(-5, 5):
        for z in range(-5, 5):
            if r.random() < .5:
                h = r.choice((3, 4, 5, 6, 7, 8))
                rot = [r.uniform(-12, 12), 0, r.uniform(-12, 12)]
                pv = [x + .5, 26.5, z + .5]
                m.cube('head', [x, 26.5, z], [1, h, 1], gm, rot=rot, pivot=pv)
                m.cube('head', [x, 26.5 + h, z], [1, 1, 1], tips, rot=rot, pivot=pv)
    spine = Mat(bone_c)
    for i, y in enumerate((16, 14, 12, 10)):
        m.cube('body', [-1.5 + (i % 2) * .5, y, -2.6], [3 - (i % 2), 1.2, 1], spine)
        m.cube('body', [-.5, y + 1.2, -2.3], [1, .8, .6], spine)
    return m, {'seed': 2121}


# ================================================================================ 22 CARVED WOOD (totem)
X8 = [
    "........",
    ".XX..XX.",
    "..XXXX..",
    "...XX...",
    "..XXXX..",
    ".XX..XX.",
    "........",
    "........",
]
SMALLFACE = [
    "........",
    "........",
    "..E..E..",
    "..E..E..",
    "........",
    "...MM...",
    "...MM...",
    "........",
]


TOTEM_TOP = [      # chunky X carved over two eyes
    "........",
    "..X..X..",
    "...XX...",
    "..X..X..",
    ".EE..EE.",
    ".EE..EE.",
    "........",
    "........",
    "........",
]
TOTEM_MID = [      # small round eyes and a tiny mouth
    "........",
    "........",
    ".EE..EE.",
    ".EE..EE.",
    "........",
    "........",
    "...M....",
    "........",
    "........",
]
TOTEM_LOW = [      # a recessed carved panel with two eyes peeking out
    "........",
    ".SSSSSS.",
    ".S....S.",
    ".SE..ES.",
    ".S....S.",
    ".S....S.",
    ".SSSSSS.",
    "........",
]


@design('carved_wood')
def carved_wood():
    """Carved Wood Creeper, redrawn from the totem reference: three tall terracotta-wood blocks split by flush
    dark grooves, each carved with its own face, on a tilted collar and a pair of split stone feet."""
    terra = ('#b8622e', '#c66e36', '#d27a40', '#dc884a', '#e49656')
    carve = '#5e2a16'
    groove = Mat(('#7a3a1e', '#84401f', '#70341a'), blob=0)
    stone = ('#7a7a74', '#8a8a84', '#9a9a92', '#aaaaa2')

    def block(pattern):
        return Mat(terra, blob=0, overlays=[grain(('#a04e28', '#dc8c58'), prob=.25),
                                            creeper_face(carve, pattern=pattern, shade='#a85828')])
    plain = Mat(terra, blob=0, overlays=[grain(('#a04e28', '#dc8c58'), prob=.25)])
    m = Model('carved_wood', bounds=(3, 5, 1.6))
    m.bone('body', [0, 3, 0]); m.bone('head', [0, 22.5, 0], parent='body')
    feet = (('leg0', -2.4, 2), ('leg1', 2.4, 2), ('leg2', -2.4, -2), ('leg3', 2.4, -2))
    for n, x, z in feet:
        m.bone(n, [x, 3, z])
    m.cube('head', [-4, 22.5, -4], [8, 9, 8], block(TOTEM_TOP), face=True)
    m.cube('body', [-4, 13.5, -4], [8, 9, 8], block(TOTEM_MID), face=True)
    m.cube('body', [-4, 5.5, -4], [8, 8, 8], block(TOTEM_LOW), face=True)
    for y in (13.2, 22.2):  # flush grooves between the blocks
        m.cube('body', [-4.1, y, -4.1], [8.2, .6, 8.2], groove)
    m.cube('body', [-4.5, 4, -4.6], [9, 2.6, 9.2], plain, rot=[-6, 0, -7], pivot=[0, 5.3, 0])
    m.cube('body', [-4.6, 6.2, -4.7], [9.2, .6, 9.4], groove, rot=[-6, 0, -7], pivot=[0, 5.3, 0])
    m.cube('body', [-4.6, 3.8, -4.7], [9.2, .5, 9.4], groove, rot=[-6, 0, -7], pivot=[0, 5.3, 0])
    stone_m = Mat(stone, blob=1.2, blotch=(('#6a6a64', '#72726c'), .7, 1), overlays=[spots(('#5a5a54',), .1)])
    for n, x, z in feet:
        m.cube(n, [x - 1.9 + (.2 if x > 0 else -.2), 0, z - 2.5], [3.8, 4.2, 5], stone_m)
    return m, {'seed': 2222, 'cam': ([-34, 30, -46], [0, 15, 0])}


# ================================================================================ 23 SLENDER GREEN (bamboo)
EYES6 = [
    "......",
    "......",
    "......",
    "EE.EE.",
    "EE.EE.",
    "......",
    "......",
]


def bamboo_streaks(light, dark, faces=('north', 'south', 'east', 'west')):
    """Short horizontal light/dark dashes like the fibres on a bamboo block."""
    def f(img, face, rng, info):
        if face not in faces:
            return
        h, w, _ = img.shape
        for y in range(h):
            if rng.random() < .55:
                x0 = rng.integers(w)
                col = _pick(rng, light if rng.random() < .6 else dark)
                for x in range(x0, min(w, x0 + rng.integers(2, 4))):
                    img[y, x] = col
    return f


@design('slender_green')
def slender_green():
    """Slender Green, redrawn from the bamboo reference: a square bamboo-block head with small low eyes,
    a thin stalk ringed by bright pale nodes with a couple of side nubs, and a lumpy rooted foot."""
    bam = ('#5e9e1e', '#6eb024', '#80c02c', '#92ce36', '#a4da42')
    streak_l, streak_d = ('#b8e45c', '#c6ec70'), ('#4e8a18', '#558f1c')
    node = Mat(('#c8ee88', '#d6f49c', '#bce67a'), blob=0)
    node_line = Mat(('#3e7414', '#447c16'), blob=0)
    head = Mat(bam, blob=0, overlays=[bamboo_streaks(streak_l, streak_d), rings(('#c8ee88', '#d6f49c'), every=9, offset=1),
                                      creeper_face('#14280c', pattern=EYES6)])
    stalk = Mat(bam, blob=0, overlays=[bamboo_streaks(streak_l, streak_d)])
    base = Mat(bam, blob=0, overlays=[bamboo_streaks(streak_l, streak_d), cover_bottom(('#3e6e1e', '#4a7e24'), 1, .6)])
    m = Model('slender_green', bounds=(2.5, 5, 1.6))
    m.bone('body', [0, 4, 0]); m.bone('head', [0, 22, 0], parent='body')
    feet = (('leg0', -1.6, 1.6), ('leg1', 1.6, 1.6), ('leg2', -1.6, -1.6), ('leg3', 1.6, -1.6))
    for n, x, z in feet:
        m.bone(n, [x, 4, z])
    m.cube('head', [-3, 22, -3], [6, 7, 6], head, face=True)
    m.cube('head', [3, 26, -.5], [.8, 1.5, 1], stalk)              # little nub on the side of the head
    m.cube('body', [-1.5, 4, -1.5], [3, 18, 3], stalk)
    for y in (8.5, 13.5, 18.5):
        m.cube('body', [-1.6, y, -1.6], [3.2, .8, 3.2], node)
        m.cube('body', [-1.55, y - .4, -1.55], [3.1, .4, 3.1], node_line)
    m.cube('body', [1.5, 11, -.5], [1, 1.5, 1], stalk)             # side nubs where leaves would sprout
    m.cube('body', [1.5, 16, -.5], [.8, 1, 1], stalk)
    for n, x, z in feet:
        m.cube(n, [x - 1.8, 0, z - 1.8], [3.6, 4.4, 3.6], base)
        m.cube(n, [x - 1.4, 4.4, z - 1.4], [2.8, .6, 2.8], base)   # rounded shoulder of each lobe
    return m, {'seed': 2323, 'cam': ([-28, 28, -40], [0, 15, 0])}
