"""Full redo (2026-11-23) of Swamp, Crystal, Jungle, Lava, Thorn and Spore Queen.

Each design is rebuilt against its reference art and the concept target in the owner's design-protection
registry (model_protection/SCOPED_RULES.md in the GitHub repo). What is kept on purpose:
  * every creeper: the vanilla rig (bone names and pivots that animation.creeper.legs drives), the 8x8x8 head,
    the classic creeper face pattern and its place on the head, identifiers, materials and texture set;
  * Thorn: the head block and its face exactly as in the previous build (the protected "woody creeper head" and eyes);
  * Spore Queen: the draped gown, cream toes and foot moss exactly as in the previous build.
Every named feature in the registry for these six creepers is present, and each is built as its own part so it
can be compared or rolled back on its own. Previous sources: designs_more.py history / bundled baselines.
"""
import math
from forge import (Model, Mat, skeleton, cover_top, cover_bottom, veins, spots, grain, creeper_face, pal)
from designs import design, LEGS
from designs_more import leaf, pix_flower, lava_seams, molten_feet, draped_vines


# ------------------------------------------------------------------------------ shared helpers
def mask_plate(m, bone, inside, y, thick, mat, lim=10):
    """A flat plate shaped by inside(px, pz) on a 1-px grid, built as merged x-runs (one cube per run)."""
    for zi in range(-lim, lim):
        x = -lim
        while x < lim:
            if not inside(x + .5, zi + .5):
                x += 1; continue
            r = x
            while r < lim and inside(r + .5, zi + .5):
                r += 1
            m.cube(bone, [x, y, zi], [r - x, thick, 1], mat, cell=(x, zi))
            x = r


def plate_texture(inside, cx, cz, groove, rim, spokes=8, inner=1.2, rim_w=1):
    """Up-face detail for a mask plate, in model space: a darker rim along the outline and radial grooves."""
    gp, rp = pal(*groove), pal(*rim)
    def edge(px, pz):
        return any(not inside(px + dx, pz + dz) for dx in range(-rim_w, rim_w + 1) for dz in range(-rim_w, rim_w + 1) if abs(dx) + abs(dz) == rim_w)
    def f(img, face, rng, info):
        if face != 'up' or 'cell' not in info:
            return
        h, w, _ = img.shape
        x0, z0 = info['cell']
        for j in range(h):
            for i in range(w):
                px, pz = x0 + i + .5, z0 + j + .5
                if edge(px, pz):
                    img[j, i] = rp[rng.integers(len(rp))]
                    continue
                d = math.hypot(px - cx, pz - cz)
                a = math.degrees(math.atan2(pz - cz, px - cx)) % (360 / spokes)
                if d > inner and (a < 360 / spokes * .12 or a > 360 / spokes * .88):
                    img[j, i] = gp[rng.integers(len(gp))]
    return f


def shade_top(rows=2, k=(.62, .8), faces=('north',)):
    """Contact shadow along the top of a face (under a brim, cap or canopy)."""
    def f(img, face, rng, info):
        if face not in faces:
            return
        for r in range(min(rows, img.shape[0])):
            img[r] = (img[r] * k[r]).astype(img.dtype)
    return f


def strand(m, bone, x, ytop, z, length, mat, w=1, d=.6):
    m.cube(bone, [x - w / 2, ytop - length, z - d / 2], [w, length, d], mat)


def prism(m, bone, x, y, z, w, h, rot, shaft, tip, root=None):
    """Hexagonal-looking crystal: optional root collar, a shaft, and a two-step point. Rigid about its base."""
    pv = [x, y, z]
    if root is not None:
        m.cube(bone, [x - (w + .6) / 2, y - .2, z - (w + .6) / 2], [w + .6, .8, w + .6], root, rot=rot, pivot=pv)
    m.cube(bone, [x - w / 2, y, z - w / 2], [w, h, w], shaft, rot=rot, pivot=pv)
    t1 = w * .64
    m.cube(bone, [x - t1 / 2, y + h, z - t1 / 2], [t1, max(.8, h * .2), t1], tip, rot=rot, pivot=pv)
    t2 = w * .3
    m.cube(bone, [x - t2 / 2, y + h + max(.8, h * .2), z - t2 / 2], [t2, max(.6, h * .12), t2], tip, rot=rot, pivot=pv)


# ================================================================================ 04 SWAMP
@design('swamp')
def swamp():
    """Swamp Creeper: an irregular broad lily-pad crown with a front notch, a bigger right lobe and a rear overhang,
    a raised white lotus with a golden centre, moss hanging from the pad rim, a square muddy head, cattails by
    its left foot and reeds by its right foot, feet standing in swamp water."""
    mud = ('#2c2e1c', '#383b22', '#444829', '#50552f', '#5c6236')
    moss = ('#7e9a26', '#94ae2e', '#a8c23a', '#bcd44a')
    water = ('#245c5e', '#2e7074', '#3a8486')
    head = Mat(mud, blob=1, blotch=(moss, .8, 2),
               overlays=[spots(('#5a4a2a', '#66542e'), .06, 1, faces=('north',)),            # forehead mud
                         spots(('#6e8c24', '#86a42c', '#9ab83a'), .22, 1, faces=('south',)),  # algae on the back of the head
                         shade_top(2), creeper_face('#0e120a')])
    body = Mat(mud, blob=1, blotch=(moss, .78, 2), overlays=[veins(moss[:3], .5, 6)])
    leg = Mat(('#303a30', '#3a4638', '#445242', '#4e5c4a'), blob=1, blotch=(('#5e7a26', '#6e8c2a'), .8, 2),
              overlays=[cover_top(('#6e8c24', '#7e9c2a'), 1, .4, 2), cover_bottom(water, 2, .5)])
    m = skeleton(Model('swamp'), head=head, body=body, legs=leg)

    # ---- lily-pad crown: one irregular plate (main disc + right lobe + rear overhang) with a notch at the front
    pad = m.bone('lily_pad', [0, 26, 0], parent='head', rotation=[-3, 0, 2])
    def inside(px, pz):
        main = math.hypot(px - .4, pz - .6) <= 6.4
        right = math.hypot(px - 3.6, pz + .2) <= 4.3          # right lobe (viewer's right)
        rear = math.hypot(px - .2, pz - 3.2) <= 5.0            # rear overhang
        if not (main or right or rear):
            return False
        ang = math.degrees(math.atan2(pz - .6, px - .4)) % 360
        d = math.hypot(px - .4, pz - .6)
        return not (d > 1.2 and abs((ang - 258 + 180) % 360 - 180) < 12)   # the front notch
    top = ('#3f8a1e', '#4a9824', '#56a62a', '#62b232')
    pad_mat = Mat(top, blob=1.5, overlays=[plate_texture(inside, .4, .6, ('#6cbe3c', '#78c846'), ('#2a5e12', '#2f6814'), spokes=9)],
                  sides=Mat(('#2a5e12', '#306a16')), down=Mat(('#34401a', '#3c4a1e', '#2e3816')))
    mask_plate(m, pad, inside, 26, 1.2, pad_mat)

    # ---- moss hanging from the pad rim: a front fringe that leaves the eyes clear, long side strands, algae at the back
    hang = Mat(('#8aa82a', '#9cba34', '#b0cc42'), blob=0)
    hang2 = Mat(('#6a8a22', '#7c9a28'), blob=0)
    for x, ln in ((-4.5, 6), (-3.5, 1), (-2.5, 1.5), (-1.5, 1), (-.5, 3), (.5, 1.5), (1.5, 1), (2.5, 1.5), (3.5, 2), (4.5, 7)):
        strand(m, pad, x, 26, -4.6, ln, hang if ln > 1.2 else hang2)
    for z, ln in ((-3.5, 5), (-2.5, 7), (-1, 3), (0, 6), (1.5, 8), (3, 4), (4.5, 6)):
        strand(m, pad, -4.7, 26, z, ln, hang, w=.6, d=1)           # left strand curtain
    for z, ln in ((-3, 4), (-1.5, 8), (0, 5), (1, 3), (2.5, 7), (4, 5)):
        strand(m, pad, 4.7, 26, z, ln, hang, w=.6, d=1)            # right strand curtain
    for x, ln in ((-3, 4), (-1, 6), (1, 3), (3, 5)):
        strand(m, pad, x, 26, 4.7, ln, hang2)                      # back-of-head algae
    for x, z, ln in ((-5.8, -.5, 4), (6.5, -2.8, 5), (7.2, 1, 3), (2, 7.4, 4), (-3.5, 5.6, 3), (5, 4.6, 4)):
        strand(m, pad, x, 26, z, ln, hang, w=.8, d=.8)             # strands dripping off the outer rim

    # ---- raised white lotus: green base and stem, outer and inner white petals, golden centre
    lx, ly, lz = 1.4, 27.2, 1.8
    lotus = m.bone('lotus', [lx, ly, lz], parent=pad)
    stem = Mat(('#4e8a22', '#5a9a28'), blob=0)
    m.cube(lotus, [lx - .4, ly - 1, lz - .4], [.8, 1.3, .8], stem)
    m.cube(lotus, [lx - 1.3, ly, lz - 1.3], [2.6, .5, 2.6], Mat(('#5a9a28', '#68a830'), blob=0))
    white = Mat(('#f2ecec', '#fbf6f6', '#fffcfc'), blob=0)
    blush = Mat(('#f4c6d4', '#f8d4de', '#fbe2ea'), blob=0)
    for i in range(8):
        leaf(m, lotus, lx, ly + .4, lz, 3.1, i * 45 + 22, -30, white if i % 2 else blush, width=1.6, thick=.5, start=.4)
    for i in range(6):
        leaf(m, lotus, lx, ly + .5, lz, 2.4, i * 60, -62, blush if i % 2 else white, width=1.3, thick=.45, start=.2)
    m.cube(lotus, [lx - .6, ly + .5, lz - .6], [1.2, 1.4, 1.2], Mat(('#f0b828', '#ffd040', '#ffe070'), blob=0))

    # ---- cattails by the left foot (viewer's right) and short reeds by the right foot
    green, tail = Mat(('#5a8a26', '#6c9e2e'), blob=0), Mat(('#5e3818', '#74461e', '#86542a'), blob=0)
    for x, z, h in ((4.7, -5.2, 7), (5.6, -3.6, 9.5), (4.9, -2.2, 6)):
        m.cube('leg3', [x - .4, 0, z - .4], [.8, h, .8], green)
        m.cube('leg3', [x - .7, h - .6, z - .7], [1.4, 2.6, 1.4], tail)
        m.cube('leg3', [x - .2, h + 2, z - .2], [.4, .9, .4], green)
    m.cube('leg3', [5.6, 0, -6.2], [.5, 5, .5], green, rot=[-12, 0, -10], pivot=[5.8, 0, -6])
    for x, z, h, rz in ((-4.6, -6.0, 4, 10), (-5.2, -4.8, 3, 18), (-4.4, -3.6, 5, 4)):
        m.cube('leg2', [x - .25, 0, z - .25], [.5, h, .5], green, rot=[0, 0, rz], pivot=[x, 0, z])
    return m, {'seed': 404, 'bounds': (4.5, 5.0, 1.6)}


# ================================================================================ 03 CRYSTAL
@design('crystal')
def crystal_creeper():
    """Crystal Creeper: lavender amethyst stone with purple mottling, asymmetric connected crystal clusters bursting
    from the top and right of the head (central crown with the tallest crystal, left, right and rear fans) and big
    clusters around the feet, with the face and the gaps between crystals left readable."""
    stone = ('#9a8ab4', '#aa9cc4', '#baaed2', '#c9bfdf', '#d8d0ea')
    mott = ('#8a62bc', '#9a74cc', '#ad8ad8')
    shaft = Mat(('#7440b4', '#8a52cc', '#a268e0', '#b880ee'), blob=0)
    tip = Mat(('#c898f6', '#dcb4fc', '#eed6ff'), blob=0)
    root = Mat(('#5a3290', '#663a9e'), blob=0)
    head = Mat(stone, blob=1, blotch=(mott, .76, 1), overlays=[creeper_face('#33264a')])
    body = Mat(stone, blob=1, blotch=(mott, .72, 1), overlays=[veins(mott, .6, 5)])
    leg = Mat(stone, blob=1, blotch=(mott, .74, 1))
    m = skeleton(Model('crystal'), head=head, body=body, legs=leg)
    m.glows(('#a268e0', '#b880ee', '#c898f6', '#dcb4fc', '#eed6ff'))
    crown = m.bone('crystal_crown', [0, 26, 0], parent='head')
    # central crown with the tallest crystal, a little right of centre and leaning back-right
    prism(m, crown, 1.6, 26, .6, 2.6, 8.5, [6, 0, -12], shaft, tip, root)
    prism(m, crown, -.4, 26, -.4, 2, 5.5, [-8, 0, 6], shaft, tip, root)
    # right fan: the biggest crystals, leaning out over the right side of the head
    prism(m, crown, 3.2, 26, -1.6, 2.4, 7, [-10, 0, -34], shaft, tip, root)
    prism(m, crown, 3.4, 25.5, 2, 2.2, 6, [14, 0, -50], shaft, tip, root)
    prism(m, crown, 4.1, 22.5, -.4, 1.6, 4, [0, 0, -74], shaft, tip)
    # left fan: two small crystals, kept low so the face stays clear
    prism(m, crown, -2.6, 26, 1.6, 1.6, 3.6, [12, 0, 28], shaft, tip, root)
    prism(m, crown, -3.2, 26, -1.4, 1.1, 2.2, [-10, 0, 40], shaft, tip)
    # rear fan
    prism(m, crown, .8, 26, 3.1, 2, 5.5, [34, 0, -10], shaft, tip, root)
    prism(m, crown, -1.4, 25.2, 3.6, 1.4, 3.4, [52, 0, 14], shaft, tip)
    # clusters around the feet: big at the front-left and front-right, smaller at the back
    clusters = (('leg2', -4.3, -4.6, ((2.2, 7, [-12, 0, 24]), (1.6, 4, [-28, 0, 8]), (1.2, 3, [4, 0, 46]))),
                ('leg3', 4.3, -2.8, ((2.4, 8, [-8, 0, -20]), (1.6, 4.5, [12, 0, -40]), (1.2, 3, [-30, 0, -14]))),
                ('leg1', 4.2, 5, ((1.6, 4, [24, 0, -26]), (1.1, 2.4, [6, 0, -48]))),
                ('leg0', -4.2, 5.2, ((1.4, 3, [30, 0, 22]),)))
    for name, x, z, cs in clusters:
        for k, (w, h, rot) in enumerate(cs):
            prism(m, name, x + (k % 2) * .5 * (1 if x > 0 else -1), .3, z + (k - 1) * .9, w, h, rot, shaft, tip, root if k == 0 else None)
    return m, {'seed': 303, 'alt': ((.95, .9, 1.0), (0, 0, 0)), 'bounds': (4.5, 5.2, 1.7)}


# ================================================================================ 07 JUNGLE
def frond(m, bone, x, y, z, yaw, segs, w, mat, thick=.6, start=0):
    """A broad tropical leaf that arches out and droops: segs = ((length, droop_deg), ...), each segment narrower.
    yaw 0 points to +x (viewer's right), 90 to the front (-z), 180 to -x, 270 to the back."""
    b = m.bone(f'{bone}_leaf{len(m.bones)}', [x, y, z], parent=bone, rotation=[0, yaw, 0])
    px, py = x + start, y
    for k, (ln, dr) in enumerate(segs):
        ww = w * (1 - .22 * k)
        m.cube(b, [px, py - thick / 2, z - ww / 2], [ln, thick, ww], mat, rot=[0, 0, -dr], pivot=[px, py, z])
        px += ln * math.cos(math.radians(dr)) * .96
        py -= ln * math.sin(math.radians(dr)) * .96
    return b


@design('jungle')
def jungle():
    """Jungle Creeper: a wide tropical umbrella canopy (rounded top leaf mass, broad drooping fronds front-left,
    front-right, sides and a rear fan, a long hanging leaf at the back) that keeps the eyes clear, one large red
    hibiscus at the top-right corner, vines hanging on both sides, a leafy belt at the waist, a bark stalk wrapped
    in vines and root-covered feet."""
    leafc = ('#3e6e1c', '#4c8424', '#5c982c', '#6eac36', '#84c042')
    headc = ('#4e7e22', '#5c9028', '#6ca232', '#7cb23a', '#8ec246')
    bark = ('#4a2e18', '#5c3c1e', '#704a26', '#82582e')
    vine = ('#4a7c20', '#5c9428', '#72aa32')
    lm = Mat(leafc, blob=0, overlays=[veins(('#2c5614', '#356218'), .5, 6, branch=0, faces=('up',))], down=Mat(leafc[:3]))
    lm2 = Mat(('#5aa02e', '#6ab436', '#7cc440', '#8ed24c'), blob=0, overlays=[veins(('#3c7a1c',), .5, 5, branch=0, faces=('up',))],
              down=Mat(leafc[1:4]))
    vm = Mat(vine, blob=0)
    head = Mat(headc, blob=1, blotch=(('#3c6a1a', '#46781e'), .8, 1),
               overlays=[spots(('#a2d050',), .04), cover_top(leafc[1:], 1, .55, 2), shade_top(2), creeper_face('#12200c')])
    body = Mat(bark, blob=0, overlays=[grain(('#3a2210', '#946436')), veins(vine, .8, 8, branch=.1)])
    leg = Mat(leafc, blob=1, blotch=(bark, .74, 1), overlays=[veins(vine, .4, 4), cover_top(leafc[2:], 1, .4, 1)])
    m = skeleton(Model('jungle'), head=head, body=body, legs=leg)
    canopy = m.bone('canopy', [0, 26, 0], parent='head')
    # rounded top leaf mass
    m.cube(canopy, [-4.6, 26, -4.6], [9.2, 1.4, 9.2], lm)
    m.cube(canopy, [-3.6, 27.4, -3.4], [7.2, 1.3, 7.2], lm2)
    m.cube(canopy, [-2.2, 28.7, -1.8], [4.4, 1, 4.4], lm)
    # broad fronds: short visor at the front (eyes stay open), long drooping leaves everywhere else
    for yaw, segs, w, mat in ((90, ((3.6, -4), (2, 30)), 4.4, lm2),                      # front visor
                              (28, ((4.4, -10), (3.6, 18), (2.6, 48)), 4.8, lm),         # front-right canopy leaf
                              (130, ((4.4, -10), (3.6, 18), (2.6, 48)), 4.8, lm),        # front-left canopy leaf
                              (8, ((4.4, -8), (3.8, 24), (3, 58)), 4.4, lm2),            # right drooping frond
                              (174, ((4.4, -8), (4, 26), (3.2, 62)), 4.4, lm2),          # left drooping frond
                              (225, ((4.6, -10), (3.8, 20), (2.6, 52)), 4.8, lm),        # rear leaf fan
                              (270, ((4.6, -12), (3.8, 16), (2.6, 48)), 5, lm2),
                              (315, ((4.6, -10), (3.8, 20), (2.6, 52)), 4.8, lm)):
        frond(m, canopy, 0, 28.2, 0, yaw, segs, w, mat, start=1)
    for yaw in (25, 155, 245, 295):                                                     # upper tier
        frond(m, canopy, 0, 29.6, .4, yaw, ((3.4, -14), (2.6, 22)), 3.6, lm2 if yaw % 50 else lm, start=.5)
    m.cube(canopy, [-1.3, 17.5, 5.6], [2.6, 9.5, .5], lm, rot=[10, 0, 0], pivot=[0, 27, 5.6])   # long centre hanging leaf
    # one large red hibiscus at the top-right corner, with its stem tucked into the canopy
    red, redd, yel = Mat(('#d01e2a', '#e8343a', '#f24c4c'), blob=0), Mat(('#9c1220', '#b0182a'), blob=0), Mat(('#ffd23a', '#ffe680'), blob=0)
    m.cube(canopy, [3, 26.4, -5.4], [.6, .6, 1.6], vm)
    pix_flower(m, canopy, (3.3, 27.2, -5.7), red, yel, 7, px=.85, edge=redd, pitch=14)
    m.cube(canopy, [3.1, 27, -7.2], [.4, .4, 1.2], yel)
    # vines: long on the left side, shorter on the right, a few over the back
    for x, z, h in ((-4.7, -3.2, 9), (-4.7, -1.4, 12), (-4.7, .6, 7), (-4.7, 2.6, 11), (-6.8, -.6, 13), (-7.4, 2.2, 9)):
        m.cube(canopy, [x - .3, 26 - h, z - .5], [.6, h, 1], vm)
        m.cube(canopy, [x - .5, 26 - h, z - .9], [1, 1.2, 1.8], lm2)      # leaf tuft at the end
    for x, z, h in ((4.7, -2.6, 5), (4.7, .4, 7), (4.7, 2.8, 4), (6.9, 1.2, 8)):
        m.cube(canopy, [x - .3, 26 - h, z - .5], [.6, h, 1], vm)
        m.cube(canopy, [x - .5, 26 - h, z - .9], [1, 1.2, 1.8], lm2)
    # stalk: vines spiralling round the bark
    sides = ('north', 'south', 'east', 'west')
    m.cube('body', [-4.3, 9, -2.3], [8.6, 1, 4.6], vm, rot=[0, 0, 22], pivot=[0, 9.5, 0], faces=sides)
    m.cube('body', [-4.3, 14.5, -2.3], [8.6, 1, 4.6], vm, rot=[0, 0, -20], pivot=[0, 15, 0], faces=sides)
    # waist foliage belt
    for i in range(8):
        frond(m, 'body', 0, 7.4, 0, i * 45 + 22, ((3.2, 30), (1.6, 60)), 2.4, lm if i % 2 else lm2, thick=.5, start=1.6)
    # root-covered feet: bark roots running down over each foot
    root = Mat(bark[1:], blob=0)
    for name, x, z in LEGS:
        fz = z - 2.15 if z < 0 else z + 1.75
        m.cube(name, [x - 1.6, 0, fz], [.8, 6, .4], root)
        m.cube(name, [x + .6, 0, fz], [.8, 4, .4], root)
        sx = 1 if x > 0 else -1
        m.cube(name, [x + sx * 2.05 - .2, 0, z - .4], [.4, 5, .8], root)
    return m, {'seed': 707, 'bounds': (5.0, 5.2, 1.7)}


# ================================================================================ 13 LAVA
def fissure(core, halo, y_frac, faces=('north', 'south', 'east', 'west')):
    """A jagged horizontal magma fissure across a face (wanders a pixel up/down, bright core, dim edge)."""
    cp, hp = pal(*core), pal(*halo)
    def f(img, face, rng, info):
        if face not in faces:
            return
        h, w, _ = img.shape
        y = int(y_frac * h)
        for x in range(w):
            if rng.random() < .3:
                y = max(1, min(h - 2, y + (1 if rng.random() < .5 else -1)))
            img[y, x] = cp[rng.integers(len(cp))]
            if rng.random() < .6:
                img[y - 1, x] = hp[rng.integers(len(hp))]
            if rng.random() < .4:
                img[y + 1, x] = hp[rng.integers(len(hp))]
    return f


@design('lava')
def lava():
    """Lava Creeper: a heavy dark basalt head with a plain basalt forehead, a molten crown physically fused to the
    top (left lobe, centre ridge, tall right lobe leaning back-right, rear crown), a drip between the eyes, lava
    streams down both cheeks, a molten neck joint, a connected magma seam network with two torso fissures, glowing
    leg junctions and feet standing in their own glow. Embers are a walking trail."""
    rock = ('#281c1e', '#342628', '#403032', '#4c3a3c', '#584446')
    core = ('#ffb83a', '#ffc94c', '#ffa62e')
    halo = ('#e2560e', '#f06a14', '#d84a10')
    hot = ('#ffe27a', '#fff0a0')
    red = Mat(('#c83c0c', '#d8460e', '#e85a12'), blob=0, flat=True)
    ora = Mat(('#f47a16', '#ff9022', '#f8861c'), blob=0, flat=True)
    yel = Mat(('#ffb83a', '#ffcc50', '#ffd862'), blob=0, flat=True)
    tip = Mat(hot, blob=0, flat=True)
    head = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 3, 5, .7, keep_clear=(.0, .0, 1.0, 1.0)), creeper_face('#120808')])
    body = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 3, 6, .45), fissure(core, halo, .28), fissure(core, halo, .7)])
    leg = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 2, 4, .4), molten_feet(core + hot, halo, 3)])
    m = skeleton(Model('lava'), head=head, body=body, legs=leg)
    m.glows(core, halo, hot)
    crown = m.bone('molten_crown', [0, 26, 0], parent='head')
    m.cube(crown, [-4.05, 25.95, -4.05], [8.1, .7, 8.1], red)                   # crown attachment: fused molten sheet
    def stack(layers, dx=0, dz=0):
        y = 26.6
        for k, (x0, z0, w, d, h, mat) in enumerate(layers):
            m.cube(crown, [x0 + dx * k, y, z0 + dz * k], [w, h, d], mat)
            y += h
    stack(((-4, -3.6, 3, 6.6, 1.4, red), (-3.6, -2.6, 2.4, 4.6, 1.6, ora), (-3.3, -1.6, 1.6, 2.8, 1.4, yel),
           (-3, -.8, .8, 1.2, 1, tip)))                                                                             # left lobe
    stack(((-1.4, -3.8, 3, 7.2, 1.8, red), (-1.1, -2.8, 2.4, 5.4, 2.2, ora), (-.8, -1.8, 1.6, 3.4, 2, yel),
           (-.5, -1, .9, 1.6, 1.4, tip)))                                                                           # centre ridge
    stack(((.8, -3.8, 3.4, 7.6, 2.2, red), (1, -3, 3.2, 6.4, 2.4, ora), (1.2, -2.2, 2.8, 5, 2.2, ora),
           (1.4, -1.4, 2.4, 3.6, 2, yel), (1.6, -.6, 1.8, 2.4, 1.6, tip)), dx=.3, dz=.45)                           # right lobe
    stack(((-3.8, 2.2, 7.6, 1.9, 1.6, red), (-3, 2.6, 6, 1.4, 1.8, ora), (-1.6, 2.9, 3.2, .9, 1.4, yel)))            # rear crown
    m.cube(crown, [3.9, 24.5, -3.9], [.6, 2.4, .6], ora)                       # tongues licking down the right corners
    m.cube(crown, [3.9, 25, 2.6], [.6, 1.8, .6], ora)
    for x, y, z in ((3.8, 38.4, 2.4), (1.2, 36.6, -.2), (-2.6, 33.4, 1), (4.6, 35, -1.6)):
        m.cube(crown, [x, y, z], [.6, .6, .6], tip)                                                                  # sparks
    m.cube('head', [-.5, 22.6, -4.3], [1, 3.4, .4], ora)                       # front drip between the eyes
    m.cube('head', [-.35, 22.2, -4.35], [.7, .6, .4], yel)
    m.cube('head', [4, 19.2, -2.4], [.4, 6.8, 1.2], ora)                       # right cheek streams
    m.cube('head', [4.05, 21, 1], [.4, 5, 1], red)
    m.cube('head', [4.05, 18.6, -2.2], [.4, .8, .8], yel)
    m.cube('head', [-4.4, 20.4, -1.8], [.4, 5.6, 1], ora)                      # left cheek stream
    m.cube('head', [-4.45, 22.4, 1.4], [.4, 3.6, .8], red)
    m.cube('body', [-3.4, 17.5, -2.15], [6.8, .6, 4.3], ora)                   # head-to-neck molten connection
    for name, x, z in LEGS:                                                    # glowing front leg junctions
        if z < 0:
            m.cube(name, [x - 1.8, 5.3, z - 2.25], [3.6, .5, .3], ora)
    return m, {'seed': 1313, 'alt': ((1, .9, .85), (0, 0, 0))}


# ------------------------------------------------------------------------------ protected parts
import json as _json
import pathlib as _pathlib
import numpy as _np
from PIL import Image as _Image
PROTECTED = _pathlib.Path(__file__).resolve().parent / 'protected'


def apply_keep(geo, img, opts):
    """Copy protected parts pixel-for-pixel from the stored baseline (tools/protected/<key>_creeper.*).
    opts['keep'] = (key, [(bone, origin, size), ...]). Every listed part must exist with the same bone, origin,
    size, rotation and pivot in both the new geometry and the baseline, or the build stops."""
    if 'keep' not in opts:
        return img
    key, parts = opts['keep']
    old = _json.loads((PROTECTED / f'{key}_creeper.geo.json').read_text())['minecraft:geometry'][0]
    old_img = _np.array(_Image.open(PROTECTED / f'{key}_creeper.png').convert('RGBA'))
    new = _np.array(img)
    def index(g):
        out = {}
        for b in g['bones']:
            for c in b.get('cubes', []):
                out[(b['name'], tuple(c['origin']), tuple(c['size']))] = c
        return out
    oi, ni = index(old), index(geo['minecraft:geometry'][0])
    for bone, origin, size in parts:
        k = (bone, tuple(map(float, origin)), tuple(map(float, size)))
        oc, nc = oi.get(k), ni.get(k)
        assert oc is not None and nc is not None, f'protected part missing: {k}'
        assert oc.get('rotation') == nc.get('rotation') and oc.get('pivot') == nc.get('pivot'), f'protected part moved: {k}'
        for face, ouv in oc['uv'].items():
            nuv = nc['uv'][face]
            (ox, oy), (w, h) = ouv['uv'], ouv['uv_size']
            (nx, ny), (w2, h2) = nuv['uv'], nuv['uv_size']
            assert (w, h) == (w2, h2)
            new[int(ny):int(ny + h), int(nx):int(nx + w)] = old_img[int(oy):int(oy + h), int(ox):int(ox + w)]
    return _Image.fromarray(new, 'RGBA')


# ================================================================================ 15 THORN
@design('thorn')
def thorn():
    """Thorn Creeper: the protected mossy head block and face are kept exactly; around them a braided thorny wreath
    sends long, unevenly tapered ivory thorns out in every direction with clear gaps between them, a woody stalk
    leans forward under vines that spiral round it, roots run from the stalk down into mossy bark feet, and more
    thorns jut from the flanks and back feet."""
    green = ('#56802a', '#628e30', '#6e9c36', '#7aa83c', '#88b444')
    moss = ('#6e9a2a', '#84ae32', '#98c03c')
    wood = ('#3e2516', '#4c2e1a', '#5a3820', '#684226')
    vine_g = ('#8aa830', '#9cba3a', '#aec846')
    vine_b = ('#5a3a24', '#6c4a30', '#7e5a3a')
    vg, vb = Mat(vine_g, blob=0), Mat(vine_b, blob=0, overlays=[spots(('#3e2616',), .15)])
    leafm = Mat(('#5e8e26', '#6ea02e', '#80b236'), blob=0)
    # kept exactly (protected): the head block and its face
    head = Mat(green, blob=1, blotch=(('#4a7226', '#527a28'), .82, 1),
               overlays=[cover_top(moss, 1, .4, 2), draped_vines(vine_g, vine_b, 3), creeper_face('#14200c')])
    body = Mat(wood, blob=0, overlays=[grain(('#2c1a0c', '#7a5234')), draped_vines(vine_g, vine_b, 2)])
    leg = Mat(wood, blob=0, overlays=[grain(('#2c1a0c', '#7a5234')), cover_top(moss, 3, .5, 1)], up=Mat(moss))
    m = skeleton(Model('thorn'), head=head, body=body, legs=leg)
    ivory = (Mat(('#9c7c5e', '#a88866'), blob=0), Mat(('#d8c4a4', '#e2ceb0', '#d0b896'), blob=0), Mat(('#f4e8d0', '#fcf4e2'), blob=0))

    def thorn(bone, x, y, z, rot, k):
        """Unevenly tapered ivory thorn: brown collar, pale body, long sharp cream point."""
        pv = [x, y, z]
        base, mid, tip = ivory
        m.cube(bone, [x - .8 * k, y, z - .8 * k], [1.6 * k, 1.1 * k, 1.6 * k], base, rot=rot, pivot=pv)
        m.cube(bone, [x - .55 * k, y + 1.1 * k, z - .55 * k], [1.1 * k, 1.5 * k, 1.1 * k], mid, rot=rot, pivot=pv)
        m.cube(bone, [x - .3 * k, y + 2.6 * k, z - .3 * k], [.6 * k, 1.6 * k, .6 * k], tip, rot=rot, pivot=pv)
        m.cube(bone, [x - .12 * k, y + 4.2 * k, z - .12 * k], [.24 * k, .9 * k, .24 * k], tip, rot=rot, pivot=pv)

    # ---- braided thorny wreath round the top of the head, with leaves tucked in
    wreath = m.bone('thorn_wreath', [0, 25, 0], parent='head')
    for y, mat, th, out in ((25.2, vb, 1.3, 4.5), (24.5, vg, .7, 4.35)):
        for tilt, (o, sz, pv) in zip((4, -4, 4, -4), (
                ([-out, y, -out], [2 * out, th, .9], [0, y, -out]), ([-out, y, out - .9], [2 * out, th, .9], [0, y, out]),
                ([-out, y, -out], [.9, th, 2 * out], [-out, y, 0]), ([out - .9, y, -out], [.9, th, 2 * out], [out, y, 0]))):
            rot = [0, 0, tilt] if sz[0] > 1 else [tilt, 0, 0]
            m.cube(wreath, o, sz, mat, rot=rot, pivot=pv)
    for x, z in ((-2.5, -4.7), (2.8, 4.7), (4.7, .8), (-4.7, -1.5)):
        m.cube(wreath, [x - .8, 25.6, z - .5], [1.6, .5, 1], leafm)
    # long thorns radiating from the wreath: corners point out diagonally, edges straight out, a few up
    for x, y, z, rot, k in ((4.3, 25.6, -4.3, [-50, 0, -50], 1.4), (-4.3, 25.6, -4.3, [-55, 0, 45], 1.15),
                            (4.3, 25.6, 4.3, [50, 0, -55], 1.3), (-4.3, 25.6, 4.3, [45, 0, 50], 1.45),
                            (4.5, 25.4, 1, [0, 0, -72], 1.2), (-4.5, 25.4, -.6, [0, 0, 68], 1),
                            (1.2, 25.4, 4.5, [70, 0, 0], 1.1), (-1.8, 26, 1.6, [16, 0, 20], 1.25),
                            (1.6, 26, .4, [6, 0, -24], 1.05)):
        thorn(wreath, x, y, z, rot, k)

    # ---- woody stalk leaning forward: bark plates stepping out at the front, vines spiralling round it
    m.cube('body', [-3.6, 13, -2.6], [7.2, 5, .6], Mat(wood, blob=0, overlays=[grain(('#2c1a0c', '#7a5234'))]))
    m.cube('body', [-3.2, 15, -3], [6.4, 3, .4], Mat(wood[1:], blob=0))
    for z in (-2.7, 1.7):
        m.cube('body', [-4.8, 12, z], [9.6, .8, .9], vg, rot=[0, 0, 48], pivot=[0, 12, z])
        m.cube('body', [-4.8, 12, z], [9.6, .7, .9], vb, rot=[0, 0, -44], pivot=[0, 12, z])
    for x in (-4.3, 3.6):
        m.cube('body', [x, 8, -2.2], [.7, 9, .7], vg)
    # flank thorns: uneven, pointing out and up, with gaps between them
    for x, y, z, rot, k in ((4, 15.5, -.4, [0, 0, -66], 1.2), (-4, 11.5, .4, [0, 0, 70], 1.15),
                            (4, 9, .6, [10, 0, -80], .8), (-4, 16.5, -.6, [-8, 0, 58], .85), (0, 10, 2.1, [72, 0, 0], .75)):
        thorn('body', x, y, z, rot, k)
    # ---- roots running from the stalk down into each foot
    root = Mat(('#4a2c18', '#5a3820', '#6a4428'), blob=0)
    for name, x, z in LEGS:
        sx, sz = (1 if x > 0 else -1), (1 if z > 0 else -1)
        m.cube(name, [x - .4 + sx * .6, 3, z - sz * 1.6], [.8, 4, .8], root, rot=[sz * 25, 0, -sx * 20], pivot=[x, 7, z - sz * 2])
        m.cube(name, [x + sx * 2 - .3, 0, z - .4], [.6, 4.5, .8], root)
    # ---- a thorn jutting from each back foot
    for name, x, z in LEGS:
        if z > 0:
            sx = 1 if x > 0 else -1
            thorn(name, x + sx * 2, 3.5, z + 1, [20, 0, -sx * 62], .85)
    keep = [('head', [-4, 18, -4], [8, 8, 8])]
    return m, {'seed': 1515, 'bounds': (4.5, 5.2, 1.6), 'keep': ('thorn', keep)}


# ================================================================================ 20 SPORE QUEEN
def gills(lines, base, cx=0, cz=0, spokes=28):
    """Underside of the cap: radial gill lines in model space, on the down face of each cap strip."""
    lp, bp = pal(*lines), pal(*base)
    def f(img, face, rng, info):
        if face != 'down' or 'cell' not in info:
            return
        h, w, _ = img.shape
        x0, z0 = info['cell']
        for j in range(h):
            for i in range(w):
                px, pz = x0 + i + .5, z0 + (h - 1 - j) + .5
                a = math.degrees(math.atan2(pz - cz, px - cx)) % (360 / spokes)
                img[j, i] = lp[rng.integers(len(lp))] if a < 360 / spokes * .35 else bp[rng.integers(len(bp))]
    return f


@design('spore_queen')
def spore_queen():
    """Spore Queen: a broad rounded peach-pink cap with a scalloped edge of separate lobes, three tiers rising to a
    raised mossy centre, purple gills underneath, hooked spore tendrils hanging from the rim, a soft shadow over the
    face and a pale stalk. Kept exactly (protected): the draped violet gown with its train, and the cream toes with
    their foot moss. Small pink mushrooms grow at her feet; glowing spores drift around her."""
    cream = ('#d9cba8', '#e5d8b8', '#efe4c8', '#f7eed8')
    vine = ('#5a8a28', '#6e9e30', '#84b23a')
    orange = ('#d4683e', '#e07e4c', '#ec9660', '#f4ae76')
    purple = ('#6e3c8e', '#8650a8', '#9e66c0', '#b680d4')
    robe = Mat(purple, blob=1, overlays=[cover_bottom(orange[1:], 1, .6), veins(('#c896e0',), .4, 6)], up=Mat(purple[1:]))
    head = Mat(cream, blob=0, overlays=[veins(vine, .4, 5), shade_top(2, (.66, .84)), creeper_face('#3a2040')])
    body = Mat(cream, blob=0, overlays=[veins(vine, 1.4, 10, branch=.2)])
    leg = Mat(cream, blob=0, blotch=(vine, .7, 1))
    m = skeleton(Model('spore_queen'), head=head, body=body, legs=leg)
    m.glows(('#e49af0', '#f4c4ff'))

    # ---- the cap: scalloped lobes, three tiers and a raised centre, gills underneath
    cap = m.bone('cap', [0, 26, 0], parent='head')
    def lobed(r, n=7, depth=.9, phase=0):
        def inside(px, pz):
            a = math.atan2(pz, px)
            return math.hypot(px, pz) <= r - depth * abs(math.sin(n * a / 2 + phase))
        return inside
    gill = Mat(('#5e3478',), blob=0, overlays=[gills(('#3e1e56', '#4a2662'), ('#6a3c86', '#7a4896'))])
    rim = Mat(('#a04a8a', '#b05896', '#c066a0'), blob=0, down=gill, sides=Mat(('#8a3c7c', '#9a4888'), blob=0))
    under = Mat(('#dc6e54', '#e68262', '#ee9470', '#f4a680'), blob=1, overlays=[spots(('#fcc8a8', '#ffd8bc'), .06)],
                down=gill, sides=Mat(('#c8566c', '#d26676'), blob=0))
    mask_plate(m, cap, lobed(9, 6, 2.0), 26.3, .7, rim, lim=10)          # purple-pink frill under the edge, gills below
    mask_plate(m, cap, lobed(8.2, 6, 1.9), 27, 1.2, under, lim=10)       # broad scalloped cap: six separate lobes
    mask_plate(m, cap, lobed(6.2, 6, 1.4, .5), 28.2, 1, Mat(('#e88866', '#f09a74', '#f6ac84'), blob=1,
               overlays=[spots(('#ffd8bc',), .05)], sides=Mat(('#dc7660', '#e4846a'), blob=0)), lim=8)
    mask_plate(m, cap, lobed(4.1, 5, .8, .3), 29.2, .9, Mat(('#f09a74', '#f6ac84', '#fabe98'), blob=1,
               sides=Mat(('#e8906e',), blob=0)), lim=6)
    m.cube(cap, [-1.7, 30.1, -1.7], [3.4, .9, 3.4], Mat(('#f6ac84', '#fcc4a0'), blob=0))               # raised centre
    mossm = Mat(vine, blob=0)
    for x, z, w in ((-1.2, .6, 1.4), (.6, -1, 1), (1.2, 1, 1.2)):
        m.cube(cap, [x - w / 2, 31, z - w / 2], [w, .5, w], mossm)
    m.cube(cap, [.4, 31, .4], [.5, 1.2, .5], Mat(cream[2:], blob=0))                                    # tiny mushroom on top
    m.cube(cap, [-.2, 32.2, -.2], [1.7, .6, 1.7], Mat(('#e470b8', '#f088c8'), blob=0))
    # ---- hooked spore tendrils hanging from the rim
    ten = Mat(('#d8b07a', '#e6c48e'), blob=0)
    for x, z, h in ((-6.4, -3.2, 5), (5.8, -4.4, 4), (6.6, 2.4, 6), (-6.8, 2, 4), (2.8, -6.4, 3), (-2.8, -6.6, 4.5), (0, 6.8, 5)):
        m.cube(cap, [x - .3, 26.3 - h, z - .3], [.6, h, .6], ten)
        m.cube(cap, [x - .3 + (.6 if x < 0 else -.6), 26.3 - h, z - .3], [.6, .6, .6], ten)
        m.cube(cap, [x - .3 + (.6 if x < 0 else -.6), 26.3 - h + .6, z - .3], [.6, .6, .6], ten)
    # ---- stalk attachment: a ring of frill where the cap meets the head, a vine climbing the stalk
    m.cube('head', [-4.3, 25.2, -4.3], [8.6, .8, 8.6], Mat(cream[1:], blob=0, overlays=[spots(('#d8c098',), .2)]))
    m.cube('body', [2.2, 6, -2.3], [.8, 12, .5], mossm)
    m.cube('body', [-3, 10, -2.3], [5.2, .8, .5], mossm)
    # ---- kept exactly (protected): the draped gown, unchanged from the previous build
    m.cube('body', [-5, 0, 2], [10, 17.5, 1], robe, rot=[-22, 0, 0], pivot=[0, 17.5, 2.5])
    m.cube('body', [-4.5, 0, 3.2], [9, 12, 1], robe, rot=[-34, 0, 0], pivot=[0, 12, 3.7])
    m.cube('body', [4, 0, -2], [1, 17.5, 6], robe, rot=[0, 0, 22], pivot=[4.5, 17.5, 0])
    m.cube('body', [5.2, 0, -1], [1, 11, 6], robe, rot=[0, 0, 34], pivot=[5.7, 11, 2])
    m.cube('body', [-5, 0, -1], [1, 16, 5], robe, rot=[0, 0, -12], pivot=[-4.5, 16, 1.5])
    m.cube('body', [-7, 0, 4], [14, 1.2, 8], robe)
    m.cube('body', [5, 0, -3], [6, 1.2, 9], robe)
    # ---- small pink mushrooms growing at her feet (the spore trail still follows her as particles)
    stem = Mat(cream[1:], blob=0)
    capm = Mat(('#d860a8', '#e676b8', '#f08cc6'), blob=0, overlays=[spots(('#ffd6ee',), .2)], down=Mat(('#a04a86',), blob=0))
    for x, z, h, r in ((-5.6, -6.4, 2.2, 1.6), (-6.8, -4.6, 1.4, 1.1), (6.4, -6, 1.8, 1.4), (-8, 5.6, 2, 1.5)):
        m.cube('body', [x - .4, 0, z - .4], [.8, h, .8], stem)
        m.cube('body', [x - r, h, z - r], [2 * r, .9, 2 * r], capm)
        m.cube('body', [x - r * .6, h + .9, z - r * .6], [1.2 * r, .5, 1.2 * r], capm)
    floaters_pts = [(-9, 30, -2), (8, 31, 1), (0, 35, -6), (9, 21, -5), (-9, 19, 4)]
    for (x, y, z) in floaters_pts:
        m.cube('head', [x - .45, y, z - .45], [.9, .9, .9], Mat(('#e49af0', '#f4c4ff')))
    keep = [('body', [-5, 0, 2], [10, 17.5, 1]), ('body', [-4.5, 0, 3.2], [9, 12, 1]), ('body', [4, 0, -2], [1, 17.5, 6]),
            ('body', [5.2, 0, -1], [1, 11, 6]), ('body', [-5, 0, -1], [1, 16, 5]), ('body', [-7, 0, 4], [14, 1.2, 8]),
            ('body', [5, 0, -3], [6, 1.2, 9]),
            ('leg0', [-4, 0, 2], [4, 6, 4]), ('leg1', [0, 0, 2], [4, 6, 4]), ('leg2', [-4, 0, -6], [4, 6, 4]), ('leg3', [0, 0, -6], [4, 6, 4])]
    return m, {'seed': 2020, 'bounds': (6, 5.8, 1.8), 'keep': ('spore_queen', keep)}
