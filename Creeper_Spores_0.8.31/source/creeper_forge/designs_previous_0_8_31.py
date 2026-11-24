"""Previous (0.8.31 first-pass) designs of Swamp, Crystal, Jungle, Lava, Thorn and Spore Queen, kept for comparison
and rollback. NOT imported: the live designs are in designs_redo.py. To roll one back, import this module after
designs_redo in designs.py (the later registration wins) and regenerate that creeper."""
from forge import (_pick, Model, Mat, skeleton, cover_top, cover_bottom, veins, spots, rings, grain, stripe_band, creeper_face, pal,
                   cracks, glow_bottom)
from designs import design, flower, drips, cap, LEGS
from designs_more import (spike, crystal, leaf, pix_flower, floaters, lava_seams, molten_feet, thorn_cone, draped_vines)


@design('swamp')
def swamp():
    mud = ('#2f3220', '#3c4026', '#4a4f2e', '#575d34', '#646a3a')
    slime = ('#7c9c22', '#94b22c', '#aac83a', '#bede4c')
    water = ('#2c6a6e', '#3a8186', '#4f999c')
    pad = Mat(('#4f9a34', '#5eac3c', '#70be46', '#82cc52'), blob=0, overlays=[veins(('#3f8028',), .3, 4, branch=0, faces=('up',))])
    sl = Mat(slime, blob=0)
    head = Mat(mud, blob=1, blotch=(slime, .84, 2), overlays=[cover_top(slime, 1, .7, 5), creeper_face('#10140c')])
    body = Mat(mud, blob=1, blotch=(slime, .82, 2), overlays=[veins(slime[:3], .5, 6)])
    leg = Mat(mud, blob=1, blotch=(slime, .8, 2), overlays=[cover_top(slime, 1, .5, 2), cover_bottom(water, 1, .6)])
    m = skeleton(Model('swamp'), head=head, body=body, legs=leg)
    # broad lily pad hat (round-ish, with a notch)
    m.cube('head', [-5.5, 26, -5.5], [11, 1, 11], pad)
    m.cube('head', [-6.5, 26, -3.5], [1, 1, 7], pad)
    m.cube('head', [5.5, 26, -3.5], [1, 1, 7], pad)
    m.cube('head', [-3.5, 26, -6.5], [7, 1, 1], pad)
    m.cube('head', [-3.5, 26, 5.5], [3, 1, 1], pad)
    drips(m, 'head', [4, 2, 6, 0, 1, 5, 3, 0, 2, 6], sl, -5, 5, 26, z_front=-5)
    drips(m, 'head', [5, 0, 3, 6, 2, 0, 4, 1, 5, 2], sl, -5, 5, 26, x_side=-5, z0=-5, z1=5)
    drips(m, 'head', [2, 6, 1, 0, 4, 5, 0, 3, 6, 1], sl, -5, 5, 26, x_side=5, z0=-5, z1=5)
    pink, pale, gold = Mat(('#ee8fb0', '#f5a8c2')), Mat(('#fcdce6', '#fff2f6')), Mat(('#f2c23a', '#ffe070'))
    # water lily: outer petals, inner cup, golden heart
    for i in range(6):
        leaf(m, 'head', 0, 27, 0, 3, i * 60, -35, pink if i % 2 else pale, width=1.6, thick=.8, start=.3)
    m.cube('head', [-1.5, 27, -1.5], [3, 1.5, 3], pale)
    for i in range(4):
        leaf(m, 'head', 0, 27.6, 0, 2, 45 + i * 90, -60, pink, width=1.2, thick=.6)
    m.cube('head', [-.5, 28.4, -.5], [1, 1, 1], gold)
    stem, tail = Mat(('#5e8a2a', '#72a032')), Mat(('#6e4220', '#83502a', '#5a3418'))
    for (bone, x, z, h) in (('leg3', 4.5, -4, 6), ('leg3', 5.5, -2.5, 8), ('leg1', 5, 3, 7)):
        m.cube(bone, [x - .5, 0, z - .5], [1, h, 1], stem)
        m.cube(bone, [x - .75, h - 1, z - .75], [1.5, 3, 1.5], tail)
        m.cube(bone, [x - .25, h + 2, z - .25], [.5, 1, .5], stem)
    m.cube('leg2', [-5.5, 0, -5], [1, 5, .5], stem)
    m.cube('leg2', [-5, 0, -6.5], [.5, 3, 1], stem)
    return m, {'seed': 404}


@design('crystal')
def crystal_creeper():
    stone = ('#857d98', '#9a92ad', '#afa7c1', '#c3bcd2', '#d6d0e2')
    purple = ('#6a3cae', '#8452cf', '#a070e6', '#bf96f6', '#dcc4ff')
    cm, ct = Mat(purple[:4], blob=0), Mat(purple[2:], blob=0)
    head = Mat(stone, blob=0, overlays=[veins(purple[2:4], .4, 4, branch=0), creeper_face('#3a3148')])
    body = Mat(stone, blob=0, overlays=[veins(purple[1:4], .9, 6)])
    leg = Mat(stone, blob=0, overlays=[veins(purple[2:4], .4, 4)])
    m = skeleton(Model('crystal'), head=head, body=body, legs=leg)
    m.glows(purple[2:])
    # crown cluster bursting from the back-right corner of the head
    for x, y, z, w, h, rx, rz in ((2.5, 26, 2, 2, 7, 10, -12), (1, 26, 0, 2, 5, -5, -4), (3.2, 26, -2, 2, 5, -15, -25),
                                  (3.5, 25, 3, 2, 6, 18, -32), (-1, 26, 2.5, 2, 4, 18, 8), (3.8, 23, 0.5, 1.5, 4, 0, -50)):
        crystal(m, 'head', x, y, z, w, h, cm, ct, rot=[rx, 0, rz])
    crystal(m, 'body', 3.5, 13, 1, 2, 4, cm, ct, rot=[10, 0, -45])
    # a crystal sprouting from every foot, leaning outward
    for name, x, z in LEGS:
        sx = 1 if x > 0 else -1
        sz = 1 if z > 0 else -1
        crystal(m, name, x + sx * 1.2, 6, z + sz * 1, 2, 5 if name in ('leg1', 'leg3') else 4, cm, ct, rot=[sz * 10, 0, -sx * 14])
        crystal(m, name, x - sx * .5, 6, z + sz * 1.3, 1, 2, cm, ct, rot=[sz * 25, 0, sx * 10])
    return m, {'seed': 303, 'alt': ((.95, .9, 1.0), (0, 0, 0))}


@design('jungle')
def jungle():
    leafc = ('#3a6a1c', '#4a8024', '#5c962c', '#70aa36', '#86c042')
    bark = ('#4e301a', '#62401f', '#784f28', '#8a5e30')
    vine = ('#4b7e22', '#5f962a', '#78ad34')
    lm = Mat(leafc, blob=0, overlays=[veins(('#2f5a16',), .3, 5, branch=0, faces=('up',))])
    vm = Mat(vine)
    head = Mat(leafc, blob=1, overlays=[spots(('#a7d454',), .05), creeper_face('#13200d')])
    body = Mat(bark, blob=0, overlays=[grain(('#3c2412', '#9a6c3a')), veins(vine, .9, 8, branch=.1)])
    leg = Mat(leafc, blob=1, blotch=(bark, .7, 1), overlays=[veins(vine, .5, 5)])
    m = skeleton(Model('jungle'), head=head, body=body, legs=leg)
    m.cube('head', [-4.5, 26, -4.5], [9, 1.5, 9], lm)
    # two tiers of drooping palm fronds
    for i in range(8):
        leaf(m, 'head', 0, 27.5, 0, 10 if i % 2 == 0 else 8, i * 45 + 10, 14, lm, width=3.5, start=2)
    for i in range(5):
        leaf(m, 'head', 0, 28.3, 0, 6, i * 72 + 35, 10, lm, width=2.5, start=.5)
    # hibiscus on the upper right of the head
    red, redd, yel = Mat(('#d8222c', '#ee3a3e', '#f45252')), Mat(('#a8141e',)), Mat(('#ffd23a', '#ffe680'))
    # hibiscus pinned to the right side of the head, petals fanned flat against it
    pix_flower(m, 'head', (4.5, 23.6, -1.8), red, yel, 7, px=.9, edge=redd, yaw=-90, yaw_pivot=(4.5, 23.6, -1.8))
    m.cube('head', [5, 24, -2], [1.4, .4, .4], yel)
    # vines spilling off the crown
    for x, z, h in ((-4.6, -3, 7), (-4.6, 1, 10), (-4.6, 3, 5), (4.1, 2, 9), (4.1, 0, 6), (-2, -4.6, 3), (2.5, -4.6, 2), (4.1, -1, 4)):
        if abs(z) > 4:
            m.cube('head', [x, 26 - h, z], [1, h, .6], vm)
        else:
            m.cube('head', [x, 26 - h, z], [.6, h, 1], vm)
    sides = ('north', 'south', 'east', 'west')
    m.cube('body', [-4.3, 8, -2.3], [8.6, 1, 4.6], vm, rot=[0, 0, 20], pivot=[0, 8.5, 0], faces=sides)
    m.cube('body', [-4.3, 14, -2.3], [8.6, 1, 4.6], vm, rot=[0, 0, -18], pivot=[0, 14.5, 0], faces=sides)
    for i in range(4):
        leaf(m, 'leg3', 2, 6, -4, 4.5, i * 90 + 20, 30, lm, width=2)
        leaf(m, 'body', 4, 15, 1, 5, i * 90 + 40, 35, lm, width=2)
        leaf(m, 'leg0', -2, 6, 4, 4, i * 90 + 60, 30, lm, width=2)
    return m, {'seed': 707, 'bounds': (4.5, 5, 1.6)}


@design('lava')
def lava():
    """Lava Creeper, redrawn from the reference: warm maroon-brown rock broken into blocks by a network of
    glowing lava seams, the whole crown of the head on fire with flames leaning to the back-right, and feet
    standing in molten glow. Embers are a walking trail."""
    rock = ('#4a3434', '#563c3c', '#624646', '#6e5050', '#785858')
    core = ('#ffb83a', '#ffc94c', '#ffa62e')
    halo = ('#e2560e', '#f06a14', '#d84a10')
    hot = ('#ffe27a', '#fff0a0')
    red = Mat(('#d8460e', '#e85a12', '#c83e0c'), blob=0, flat=True)
    ora = Mat(('#f47a16', '#ff9022', '#f8861c'), blob=0, flat=True)
    yel = Mat(('#ffb83a', '#ffcc50', '#ffd862'), blob=0, flat=True)
    tip = Mat(hot, blob=0, flat=True)
    head = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 2, 4, .8, keep_clear=(.0, .15, .75, .95)), creeper_face('#140a0a')])
    body = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 2, 3, 1.0)])
    leg = Mat(rock, blob=1, overlays=[lava_seams(core, halo, 2, 3, .7), molten_feet(core, halo, 3)])
    m = skeleton(Model('lava'), head=head, body=body, legs=leg)
    m.glows(core, halo, hot)
    # the head's crown is on fire: a molten sheet, then stepped flame layers rising toward the back-right
    m.cube('head', [-4, 26, -4], [8, .6, 8], ora)
    layers = (  # (x0, z0, w, d, h, mat)
        (-4, -4, 8, 8, 1.2, red), (-3, -2.5, 7, 6.5, 1.4, ora), (-1.5, -1, 5.5, 5, 1.6, yel),
        (.5, .5, 3.5, 3.5, 1.6, ora), (1.5, 1.5, 2.5, 2.5, 1.5, yel), (2.5, 2.5, 1.5, 1.5, 1.4, tip))
    y = 26.6
    for x0, z0, w, d, h, mat in layers:
        m.cube('head', [x0, y, z0], [w, h, d], mat)
        y += h * .8
    for x, z, h, mat in ((-3.5, 3.2, 3, ora), (3.2, -3.3, 2.5, ora), (-3.4, -3.4, 1.6, red), (3.3, .8, 3.5, yel),
                         (-1, 3.4, 3.2, yel), (3.4, 3.4, 4.5, ora)):
        m.cube('head', [x - .5, 26.6, z - .5], [1.1, h, 1.1], mat)
        m.cube('head', [x - .3, 26.6 + h, z - .3], [.7, h * .35, .7], tip)
    # lava running down the right side of the head and over the shoulder
    m.cube('head', [4, 21.5, 1.5], [.4, 4.5, 1.5], ora)
    m.cube('head', [4, 23.5, -2], [.4, 2.5, 1.2], red)
    return m, {'seed': 1313, 'alt': ((1, .9, .85), (0, 0, 0))}


@design('thorn')
def thorn():
    """Thorn Creeper, redrawn from the reference: a mossy green head bound by a tight wreath of brown thorny
    vine that bristles with slender pale thorns, vines draped over the face, a bark body crossed by green and
    brown vines with thorns on its flanks, and moss-covered bark feet."""
    green = ('#56802a', '#628e30', '#6e9c36', '#7aa83c', '#88b444')
    moss = ('#6e9a2a', '#84ae32', '#98c03c')
    wood = ('#45291a', '#55341f', '#643f25', '#734a2c')
    vine_g = ('#8aa830', '#9cba3a', '#aec846')
    vine_b = ('#5a3a24', '#6c4a30', '#7e5a3a')
    cone = (Mat(('#a8866a', '#b49272'), blob=0), Mat(('#dcc2a2', '#e4ccae', '#d6b896'), blob=0), Mat(('#f2e2c6', '#faecd4')))
    vg, vb = Mat(vine_g, blob=0), Mat(vine_b, blob=0, overlays=[spots(('#3e2616',), .15)])
    head = Mat(green, blob=1, blotch=(('#4a7226', '#527a28'), .82, 1),
               overlays=[cover_top(moss, 1, .4, 2), draped_vines(vine_g, vine_b, 3), creeper_face('#14200c')])
    body = Mat(wood, blob=0, overlays=[grain(('#33200f', '#82583a')), draped_vines(vine_g, vine_b, 2)])
    leg = Mat(wood, blob=0, overlays=[grain(('#33200f', '#82583a')), cover_top(moss, 4, .5, 1)], up=Mat(moss))
    m = skeleton(Model('thorn'), head=head, body=body, legs=leg)

    # ---- a tight wreath of thorny vine hugging the top edge of the head (brown braid with a green strand)
    for y, mat, th, out in ((25.2, vb, 1.3, 4.45), (24.6, vg, .7, 4.3)):
        for tilt, (o, sz, pv) in zip((4, -4, 4, -4), (
                ([-out, y, -out], [2 * out, th, .8], [0, y, -out]), ([-out, y, out - .8], [2 * out, th, .8], [0, y, out]),
                ([-out, y, -out], [.8, th, 2 * out], [-out, y, 0]), ([out - .8, y, -out], [.8, th, 2 * out], [out, y, 0]))):
            rot = [0, 0, tilt] if sz[0] > 1 else [tilt, 0, 0]
            m.cube('head', o, sz, mat, rot=rot, pivot=pv)
    # thorns bristling out of the wreath all round: upward on top, outward at the sides
    for x, y, z, rot, k in ((4.2, 25.5, -1.5, [0, 0, -60], 1.1), (-4.2, 25.5, 1.5, [0, 0, 60], 1.1),
                            (1.5, 25.5, -4.2, [-60, 0, 0], 1), (-1.5, 25.5, 4.2, [60, 0, 0], 1),
                            (3.6, 26, 3.6, [40, 0, -40], 1.2), (-3.6, 26, -3.6, [-40, 0, 40], 1.1),
                            (3.6, 26, -3.6, [-40, 0, -40], 1), (-3.6, 26, 3.6, [40, 0, 40], 1.2),
                            (4.2, 21.5, 2, [0, 0, -85], .8), (-4.2, 21, -2, [0, 0, 85], .8)):
        thorn_cone(m, 'head', x, y, z, rot, k, cone)

    # ---- vines crossing over the body front and back (an X), and a brown runner looping the waist
    for z in (-2.45, 1.65):
        m.cube('body', [-4.8, 12, z], [9.6, .8, .8], vg, rot=[0, 0, 48], pivot=[0, 12, z])
        m.cube('body', [-4.8, 12, z], [9.6, .7, .8], vb, rot=[0, 0, -44], pivot=[0, 12, z])
    for x, y, z, rot, k in ((4.1, 15.5, -.3, [0, 0, -70], 1.1), (-4.1, 12, .3, [0, 0, 70], 1.1),
                            (4.1, 9.5, .5, [0, 0, -78], .9), (-4.1, 16.5, -.5, [0, 0, 62], .9)):
        thorn_cone(m, 'body', x, y, z, rot, k, cone)
    # ---- a thorn poking out of each back foot
    for name, x, z in LEGS:
        if z < 0:
            continue
        sx = 1 if x > 0 else -1
        thorn_cone(m, name, x + sx * 2, 4, z + 1, [20, 0, -sx * 65], .9, cone)
    return m, {'seed': 1515, 'bounds': (4, 5, 1.6)}


@design('spore_queen')
def spore_queen():
    cream = ('#d9cba8', '#e5d8b8', '#efe4c8', '#f7eed8')
    vine = ('#5a8a28', '#6e9e30', '#84b23a')
    orange = ('#d4683e', '#e07e4c', '#ec9660', '#f4ae76')
    purple = ('#6e3c8e', '#8650a8', '#9e66c0', '#b680d4')
    capo = Mat(orange, blob=1, overlays=[spots(('#f8c896',), .05)], down=Mat(purple))
    capp = Mat(purple, blob=1, down=Mat(purple[:2]))
    robe = Mat(purple, blob=1, overlays=[cover_bottom(orange[1:], 1, .6), veins(('#c896e0',), .4, 6)], up=Mat(purple[1:]))
    head = Mat(cream, blob=0, overlays=[veins(vine, .4, 5), creeper_face('#3a2040')])
    body = Mat(cream, blob=0, overlays=[veins(vine, 1.4, 10, branch=.2)])
    leg = Mat(cream, blob=0, blotch=(vine, .7, 1))
    m = skeleton(Model('spore_queen'), head=head, body=body, legs=leg)
    m.glows(('#e49af0', '#f4c4ff'))
    # frilled cap: purple under-petals, orange over-petals fanned all round, domed centre
    def short(a):  # petals over the face (and its mirror at the back) stay short so the face shows
        return min(abs(a % 360 - 90), abs(a % 360 - 270)) < 35
    for i in range(8):
        a_ = i * 45 + 22
        leaf(m, 'head', 0, 26.6, 0, 5 if short(a_) else 9.5, a_, 4 if short(a_) else 16, capp, width=5, thick=1.2, start=3)
    for i in range(8):
        a_ = i * 45
        leaf(m, 'head', 0, 27.6, 0, 5.5 if short(a_) else 9, a_, 2 if short(a_) else 12, capo, width=5.5, thick=1.4, start=2)
    m.cube('head', [-4.5, 26, -4.5], [9, 1, 9], capp)
    m.cube('head', [-4.5, 27.5, -4.5], [9, 2, 9], capo)
    m.cube('head', [-3, 29.5, -3], [6, 1.5, 6], capp)
    m.cube('head', [-1.5, 31, -1.5], [3, 1, 3], capo)
    m.cube('head', [1, 30.5, 1], [1, 2.5, 1], Mat(vine))
    m.cube('head', [1.5, 32.5, 1], [1, 1, 1], Mat(vine))
    # dangling spore tendrils with hooked tips
    ten = Mat(('#d8b07a', '#e6c48e'))
    for x, z, h in ((-7, -4, 6), (6.5, -5, 5), (7, 3, 7), (-7.5, 2, 4), (3, -7, 4), (-3, -7, 5)):
        m.cube('head', [x, 25.5 - h, z], [.6, h, .6], ten)
        m.cube('head', [x, 25.5 - h, z], [1.4, .6, .6], ten)
    # draped cape: falls from the shoulders and flares out behind and to the right, with a train on the ground
    m.cube('body', [-5, 0, 2], [10, 17.5, 1], robe, rot=[-22, 0, 0], pivot=[0, 17.5, 2.5])
    m.cube('body', [-4.5, 0, 3.2], [9, 12, 1], robe, rot=[-34, 0, 0], pivot=[0, 12, 3.7])
    m.cube('body', [4, 0, -2], [1, 17.5, 6], robe, rot=[0, 0, 22], pivot=[4.5, 17.5, 0])
    m.cube('body', [5.2, 0, -1], [1, 11, 6], robe, rot=[0, 0, 34], pivot=[5.7, 11, 2])
    m.cube('body', [-5, 0, -1], [1, 16, 5], robe, rot=[0, 0, -12], pivot=[-4.5, 16, 1.5])
    m.cube('body', [-7, 0, 4], [14, 1.2, 8], robe)
    m.cube('body', [5, 0, -3], [6, 1.2, 9], robe)
    # The pink mushrooms at her feet are now a trail of spores she leaves behind (particles/cs_trail_spore_queen).
    floaters(m, 'head', [(-9, 30, -2), (8, 31, 1), (0, 34, -6), (9, 21, -5), (-9, 19, 4)], Mat(('#e49af0', '#f4c4ff')), .9)
    return m, {'seed': 2020, 'bounds': (5.5, 5.5, 1.8)}
