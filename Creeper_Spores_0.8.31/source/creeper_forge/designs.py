"""Per-variant creeper designs, each matched to its reference concept art."""
from forge import (Model, Mat, skeleton, cover_top, cover_bottom, veins, spots, rings, grain, stripe_band,
                   creeper_face, edge_shade, pal)

LEGS = (('leg0', -2, 4), ('leg1', 2, 4), ('leg2', -2, -4), ('leg3', 2, -4))
DESIGNS = {}


def design(key):
    def deco(fn):
        DESIGNS[key] = fn
        return fn
    return deco


# ------------------------------------------------------------------------------ shared props
def flower(m, bone, x, y, z, petal, center, stem=None, stem_h=1, big=False):
    """Little pixel flower: optional stem, a plus-shaped petal cluster, and a raised centre."""
    if stem is not None and stem_h > 0:
        m.cube(bone, [x - .5, y, z - .5], [1, stem_h, 1], stem)
    y += stem_h
    s = 3 if not big else 5
    m.cube(bone, [x - s / 2, y, z - .5], [s, 1, 1], petal)
    m.cube(bone, [x - .5, y, z - s / 2], [1, 1, s], petal)
    if big:
        m.cube(bone, [x - 1.5, y, z - 1.5], [3, 1, 3], petal)
    m.cube(bone, [x - .5, y + .5, z - .5], [1, 1, 1], center)


def drips(m, bone, rng_pattern, mat, x0, x1, y_top, z_front=None, x_side=None, z0=None, z1=None, out=.5):
    """Hanging strands along an edge. rng_pattern: list of lengths (0 = gap), applied along the edge."""
    if z_front is not None:
        for i, ln in enumerate(rng_pattern):
            x = x0 + i
            if x >= x1 or ln <= 0:
                continue
            zf = z_front - out if z_front < 0 else z_front - 1 + out
            m.cube(bone, [x, y_top - ln, zf], [1, ln, 1], mat)
    if x_side is not None:
        for i, ln in enumerate(rng_pattern):
            z = z0 + i
            if z >= z1 or ln <= 0:
                continue
            xf = x_side - out if x_side < 0 else x_side - 1 + out
            m.cube(bone, [xf, y_top - ln, z], [1, ln, 1], mat)


def cap(m, bone, cx, cz, y, w, d, h, mat, inflate=0):
    m.cube(bone, [cx - w / 2, y, cz - d / 2], [w, h, d], mat, inflate=inflate)


def leg_caps(m, mat, y=5, w=5, h=1.2, d=5):
    for name, x, z in LEGS:
        cap(m, name, x, z, y, w, d, h, mat)


# ================================================================================ 01 MOSS
@design('moss')
def moss():
    stone = ('#6c716c', '#848983', '#9a9f98', '#afb3ab', '#c4c7bf')
    mossc = ('#6f9a2a', '#88b232', '#9fc63c', '#b5d64c', '#c8e25e')
    face = '#1d2419'
    moss_m = Mat(mossc, blob=1)
    body = Mat(stone, blob=1, blotch=(mossc, .72, 2), overlays=[cover_top(mossc, depth=1, drip=.35, drip_len=3), veins(mossc[1:4], 1, 7)])
    head = Mat(stone, blob=1, blotch=(mossc, .74, 2),
               overlays=[cover_top(mossc, depth=1, drip=.55, drip_len=3), creeper_face(face)])
    leg = Mat(stone, blob=1, blotch=(mossc, .76, 2), overlays=[cover_top(mossc, depth=1, drip=.5, drip_len=2)])
    m = skeleton(Model('moss'), head=head, body=body, legs=leg)
    # thick moss mat on the crown, overhanging every edge
    m.cube('head', [-4.5, 25.5, -4.5], [9, 1.5, 9], moss_m)
    drips(m, 'head', [3, 0, 1, 2, 2, 1, 0, 4], moss_m, -4, 4, 26, z_front=-4)
    drips(m, 'head', [2, 4, 0, 1, 3, 0, 2, 3], moss_m, -4, 4, 26, x_side=-4, z0=-4, z1=4)
    drips(m, 'head', [1, 3, 2, 0, 4, 1, 0, 2], moss_m, -4, 4, 26, x_side=4, z0=-4, z1=4)
    drips(m, 'head', [2, 0, 3, 1, 0, 2, 4, 1], moss_m, -4, 4, 26, z_front=4)
    white, gold, stem = Mat(('#e9ece2', '#f7f8f1', '#ffffff')), Mat(('#e8b830', '#f4d05a')), Mat(('#4c7d22', '#5e9a2a'))
    from designs_more import pix_flower
    for x, z, sh in ((-2.5, -1.5, 2), (1.5, -2.5, 3), (2.5, 2, 1), (-1, 2.5, 2)):
        m.cube('head', [x - .5, 27, z - .5], [1, sh, 1], stem)
        pix_flower(m, 'head', (x, 27 + sh + .2, z), white, gold, 5, pitch=70, px=.6, yaw=(x * 37) % 90 - 45, yaw_pivot=(x, 27 + sh, z))
    pix_flower(m, 'head', (4.5, 24, -1.5), white, gold, 5, px=.6, yaw=-90, yaw_pivot=(4.5, 24, -1.5))
    # mossy streaks on the body, vine wrapping
    m.cube('body', [-4.4, 13, -2.4], [3, 5, 0.6], moss_m)
    m.cube('body', [1.5, 8, -2.4], [2.5, 4, 0.6], moss_m)
    m.cube('body', [3.6, 10, -2], [0.8, 6, 3], moss_m)
    leg_caps(m, moss_m, y=5.2, w=4.8, h=1, d=4.8)
    m.cube('leg3', [0.3, 6.2, -6.5], [3, 1.2, 3], moss_m)
    pix_flower(m, 'leg3', (2.5, 7.6, -5), white, gold, 5, pitch=60, px=.6)
    pix_flower(m, 'leg3', (1, 7.4, -4), white, gold, 5, pitch=75, px=.5)
    pix_flower(m, 'leg1', (2, 6.8, 4.5), white, gold, 5, pitch=80, px=.6)
    return m, {'seed': 101}


import designs_more  # noqa: E402,F401  (registers designs 02-23)
import designs_redo  # noqa: E402,F401  (2026-11-23 full redo of six creepers; overrides the older entries)
