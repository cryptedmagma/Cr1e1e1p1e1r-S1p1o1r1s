"""Creeper Forge: builds Bedrock geometry + hand-style pixel textures for Creeper Spores creepers.

Every cube gets its own per-face UV region on the atlas, and every face is painted
by a material (palette noise + overlays), so the textures read like hand-made pixel art
instead of one tiled swatch stretched over everything.
"""
import json, math, random
import numpy as np
from PIL import Image

FACES = ('north', 'south', 'east', 'west', 'up', 'down')
GLOW_ALPHA = 24  # alpha for self-lit pixels under Bedrock's entity_emissive_alpha material


def hexrgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def pal(*cols):
    return [hexrgb(c) if isinstance(c, str) else tuple(c) for c in cols]


# ----------------------------------------------------------------------------------------- noise
def smooth_noise(rng, w, h, blob=1.6):
    """Clumpy value noise in [0,1] at pixel resolution."""
    a = rng.random((h + 4, w + 4))
    k = max(1, int(round(blob)))
    for _ in range(k):
        a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5.0
    a = a[2:2 + h, 2:2 + w]
    lo, hi = a.min(), a.max()
    return (a - lo) / (hi - lo + 1e-9)


_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def _bayer(w, h):
    return np.tile(_B4, (h // 4 + 1, w // 4 + 1))[:h, :w]


SIDES = ('north', 'south', 'east', 'west')


def bake_light(img, face, glow_mask=None):
    """Bake soft top-down light into a face: brighter top lip, gentle falloff, darker underside.
    Glowing pixels are left untouched so they stay bright."""
    a = img.astype(float)
    h, w = a.shape[:2]
    if face in SIDES:
        if h >= 3:
            g = np.linspace(1.07, 0.84, h)[:, None, None]
            a *= g
            a[0] *= 1.07
        if w >= 4:  # faint vertical edge darkening for rounded-block depth
            a[:, 0] *= 0.94; a[:, -1] *= 0.94
    elif face == 'up':
        a *= 1.08
        if w >= 4 and h >= 4:
            a[0, :] *= .95; a[-1, :] *= .95; a[:, 0] *= .95; a[:, -1] *= .95
    elif face == 'down':
        a *= 0.72
    out = np.clip(a, 0, 255).astype(np.uint8)
    if glow_mask is not None:
        out[glow_mask] = img[glow_mask]
    return out


def quantize(field, palette):
    n = len(palette)
    idx = np.clip((field * n).astype(int), 0, n - 1)
    arr = np.array(palette, dtype=np.uint8)[idx]
    return arr


# ------------------------------------------------------------------------------------- materials
class Mat:
    """A paintable surface. palette: dark->light colours. blotch: (palette, threshold) secondary mix.
    overlays: list of callables f(img, face, rng, info) mutating img (h,w,3 uint8)."""

    def __init__(self, palette, blob=1.0, blotch=None, overlays=(), jitter=0.12, face_palette=None,
                 up=None, down=None, sides=None, glow=False, flat=False):
        self.palette = pal(*palette)
        self.glow = glow    # whole material is self-lit
        self.flat = flat    # skip baked lighting
        self.blob = blob
        self.blotch = blotch  # (palette, threshold, blob)
        self.overlays = list(overlays)
        self.jitter = jitter
        self.up = up        # optional Mat to use for the up face
        self.down = down
        self.sides = sides

    def paint(self, w, h, face, rng, info):
        if face == 'up' and self.up is not None:
            return self.up.paint(w, h, face, rng, info)
        if face == 'down' and self.down is not None:
            return self.down.paint(w, h, face, rng, info)
        if face in ('north', 'south', 'east', 'west') and self.sides is not None:
            return self.sides.paint(w, h, face, rng, info)
        f = smooth_noise(rng, w, h, self.blob)
        # ordered (Bayer) dither between palette steps reads as hand-placed pixel art, not TV static
        n = len(self.palette)
        f = f + (_bayer(w, h) - 0.5) * (0.9 / n) + (rng.random((h, w)) - 0.5) * self.jitter * 0.6
        img = quantize(np.clip(f, 0, 0.999), self.palette)
        if self.blotch:
            bp, thr, bb = self.blotch
            m = smooth_noise(rng, w, h, bb)
            sel = m > thr
            g = smooth_noise(rng, w, h, 0.5)
            img2 = quantize(np.clip(g + (_bayer(w, h) - .5) * (0.9 / len(bp)), 0, 0.999), pal(*bp))
            # a one-pixel contact shadow under each patch gives it thickness
            if face in ('north', 'south', 'east', 'west') and h > 2:
                below = np.zeros_like(sel); below[1:] = sel[:-1]
                shadow = below & ~sel
                img[shadow] = (img[shadow] * 0.78).astype(np.uint8)
            img[sel] = img2[sel]
        for o in self.overlays:
            o(img, face, rng, info)
        return img


# ------------------------------------------------------------------------------------- overlays
def _pick(rng, palette):
    p = pal(*palette)
    return p[rng.integers(len(p))]


def cover_top(palette, depth=2, drip=0.45, drip_len=3, up_full=True, faces=None):
    """Moss/snow/slime on top that drips down the sides."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if faces and face not in faces:
            return
        if face == 'up':
            if up_full:
                n = quantize(np.clip(smooth_noise(rng, w, h, 1), 0, .999), pal(*palette))
                img[:] = n
            return
        if face == 'down':
            return
        for x in range(w):
            d = depth + (rng.integers(1, drip_len + 1) if rng.random() < drip else 0) - (1 if rng.random() < .25 else 0)
            for y in range(min(h, max(0, d))):
                img[y, x] = _pick(rng, palette)
    return f


def cover_bottom(palette, depth=1, ragged=0.5, faces=None):
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face in ('up',) or (faces and face not in faces):
            return
        if face == 'down':
            img[:] = quantize(np.clip(smooth_noise(rng, w, h, 1), 0, .999), pal(*palette)); return
        for x in range(w):
            d = depth + (1 if rng.random() < ragged else 0)
            for y in range(max(0, h - d), h):
                img[y, x] = _pick(rng, palette)
    return f


def veins(palette, count=2, length=10, faces=None, branch=0.25, core=None):
    """Random-walk cracks (lava, sculk, end, crystal glow)."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if faces and face not in faces:
            return
        n = max(1, int(round(count * (w * h) / 64.0))) if w * h >= 16 else (1 if rng.random() < .3 else 0)
        for _ in range(n):
            x, y = rng.integers(w), rng.integers(h)
            for i in range(length):
                c = _pick(rng, core if (core and i % 3 == 1) else palette)
                img[y % h, x % w] = c
                r = rng.random()
                if r < .45: y += 1
                elif r < .7: x += 1
                elif r < .9: x -= 1
                else: y -= 1
                if not (0 <= x < w and 0 <= y < h):
                    break
                if rng.random() < branch:
                    bx, by = x, y
                    for _ in range(3):
                        bx += rng.choice([-1, 1]); by += rng.choice([-1, 0, 1])
                        if 0 <= bx < w and 0 <= by < h:
                            img[by, bx] = _pick(rng, palette)
    return f


def cracks(core, halo, count=1.0, faces=None, branch=0.18, drift=0.35, min_len=0.6):
    """Continuous seams (lava, sculk, End veins): bright 1px core wandering top-to-bottom with a
    softer halo beside it and occasional side branches. count = cracks per 8px of face width."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if faces and face not in faces:
            return
        if w * h < 6:
            if rng.random() < .25 * count:
                img[rng.integers(h), rng.integers(w)] = _pick(rng, core)
            return
        n = max(1, int(round(count * max(w, 4) / 8.0))) if rng.random() < min(1, count * 1.5) else 0
        if face in ('up', 'down'):
            n = int(rng.random() < count * .6)

        def walk(x, y, steps, dirx=0):
            side = int(rng.choice([-1, 1]))
            for _ in range(steps):
                if not (0 <= x < w and 0 <= y < h):
                    return
                img[y, x] = _pick(rng, core)
                hx = x + (side if rng.random() < .75 else -side)
                if 0 <= hx < w and rng.random() < .45 and tuple(img[y, hx]) not in pal(*core):
                    img[y, hx] = _pick(rng, halo)
                if rng.random() < branch and steps > 3:
                    walk(x + rng.choice([-1, 1]), y + 1, int(rng.integers(2, 5)), rng.choice([-1, 1]))
                y += 1
                r = rng.random()
                if dirx:
                    x += dirx if r < .7 else 0
                elif r < drift / 2:
                    x -= 1
                elif r < drift:
                    x += 1
        for _ in range(n):
            x0 = int(rng.integers(w)); y0 = int(rng.integers(0, max(1, h // 3)))
            walk(x0, y0, int(h * rng.uniform(min_len, 1.0)) + 1)
    return f


def glow_bottom(palette, depth=2, faces=SIDES):
    """Heat/light pooling up from the ground along the bottom rows."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces or h < 3:
            return
        for x in range(w):
            d = depth + int(rng.integers(0, 2)) - (1 if rng.random() < .3 else 0)
            for k in range(max(0, d)):
                y = h - 1 - k
                if 0 <= y < h:
                    img[y, x] = _pick(rng, palette[:max(1, len(palette) - k)])
    return f


def spots(palette, density=0.08, size=1, faces=None):
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if faces and face not in faces:
            return
        n = int(round(density * w * h / (size * size)))
        if n == 0 and rng.random() < density * w * h * 4:
            n = 1
        for _ in range(n):
            x, y = rng.integers(max(1, w - size + 1)), rng.integers(max(1, h - size + 1))
            c = _pick(rng, palette)
            img[y:y + size, x:x + size] = c
    return f


def rings(palette, every=6, offset=2, faces=('north', 'south', 'east', 'west')):
    """Horizontal node lines (bamboo, wood bands)."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces:
            return
        for y in range(offset, h, every):
            for x in range(w):
                img[y, x] = _pick(rng, palette)
    return f


def grain(palette, faces=('north', 'south', 'east', 'west'), prob=.35):
    """Vertical streaks (wood, bark)."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces:
            return
        for x in range(w):
            if rng.random() < prob:
                c = _pick(rng, palette)
                y0 = rng.integers(h); ln = rng.integers(2, max(3, h))
                img[y0:y0 + ln, x] = c
    return f


def edge_shade(amount=0.82, faces=('north', 'south', 'east', 'west')):
    """Darken the outer pixel ring a touch so blocks read crisply."""
    def f(img, face, rng, info):
        if face not in faces or min(img.shape[:2]) < 4:
            return
        img[-1, :] = (img[-1, :] * amount).astype(np.uint8)
    return f


def stripe_band(palette, y_frac, thick=1, faces=('north', 'south', 'east', 'west'), wobble=1):
    """A wrapped rope/vine band across the side faces."""
    def f(img, face, rng, info):
        h, w, _ = img.shape
        if face not in faces:
            return
        y = int(y_frac * h)
        for x in range(w):
            yy = y + (rng.integers(-wobble, wobble + 1) if wobble else 0) + (x // 3) % 2
            for t in range(thick):
                if 0 <= yy + t < h:
                    img[yy + t, x] = _pick(rng, palette)
    return f


# ---------------------------------------------------------------------------------- creeper face
FACE8 = [
    "........",
    "........",
    ".EE..EE.",
    ".EE..EE.",
    "...MM...",
    "..MMMM..",
    "..MMMM..",
    "..M..M..",
]


def creeper_face(eye, mouth=None, pattern=FACE8, shade=None, glow=None):
    """Stamp the classic creeper face, scaled to the face size, on the north face."""
    eye = pal(eye)[0]
    mouth = pal(mouth)[0] if mouth else eye
    shade = pal(shade)[0] if shade else None
    glow = pal(glow)[0] if glow else None

    def f(img, face, rng, info):
        if face != 'north' or not info.get('face'):
            return
        h, w, _ = img.shape
        ph, pw = len(pattern), len(pattern[0])
        sx, sy = w / pw, h / ph
        for py, row in enumerate(pattern):
            for px, ch in enumerate(row):
                if ch == '.':
                    continue
                col = {'E': eye, 'M': mouth, 'S': shade or eye, 'G': glow or eye}.get(ch, eye)
                x0, x1 = int(round(px * sx)), int(round((px + 1) * sx))
                y0, y1 = int(round(py * sy)), int(round((py + 1) * sy))
                img[y0:y1, x0:x1] = col
        if shade is not None:  # soft shadow ring right under the eyes to give depth
            pass
    return f


# ----------------------------------------------------------------------------------------- model
class Model:
    def __init__(self, key, tex=128, bounds=(3.4, 5.0, 1.55)):
        self.key = key
        self.tex = tex
        self.bones = []
        self._bones = {}
        self.cubes = []  # (bone, dict, mat, info)
        self.bounds = bounds
        self.glow = []   # RGB colours that should glow in-game (entity_emissive_alpha)

    def glows(self, *palettes):
        for p in palettes:
            self.glow.extend(pal(*p) if not isinstance(p, str) else pal(p))
        return self

    # Design code uses "intent" rotations: rz < 0 leans the top toward +x, rx > 0 leans it toward +z.
    # Bedrock (verified by rendering in Blockbench) uses the opposite sign on x and z, so convert here.
    @staticmethod
    def _rot(r):
        return [float(-r[0]), float(r[1]), float(-r[2])]

    def bone(self, name, pivot, parent=None, rotation=None):
        b = {'name': name, 'pivot': list(map(float, pivot))}
        if parent: b['parent'] = parent
        if rotation: b['rotation'] = self._rot(rotation)
        self.bones.append(b); self._bones[name] = b
        return name

    def cube(self, bone, origin, size, mat, rot=None, pivot=None, inflate=0, faces=None, **info):
        c = {'origin': [float(v) for v in origin], 'size': [float(v) for v in size]}
        if inflate: c['inflate'] = float(inflate)
        if rot is not None:
            c['rotation'] = self._rot(rot)
            if pivot is None:
                pivot = [origin[0] + size[0] / 2, origin[1], origin[2] + size[2] / 2]
            c['pivot'] = [float(v) for v in pivot]
        info['faces'] = faces
        self.cubes.append((bone, c, mat, info))
        return c

    def sym(self, bone, origin, size, mat, rot=None, pivot=None, **kw):
        """Add a cube and its mirror across x=0."""
        self.cube(bone, origin, size, mat, rot=rot, pivot=pivot, **kw)
        mo = [-(origin[0] + size[0]), origin[1], origin[2]]
        mr = None if rot is None else [rot[0], -rot[1], -rot[2]]
        mp = None if pivot is None else [-pivot[0], pivot[1], pivot[2]]
        self.cube(bone, mo, size, mat, rot=mr, pivot=mp, **kw)

    # -------------------------------------------------------------- build
    def build(self, seed=1):
        rng = np.random.default_rng(seed)
        rects = []
        for i, (bone, c, mat, info) in enumerate(self.cubes):
            sx, sy, sz = c['size']
            dims = {'north': (sx, sy), 'south': (sx, sy), 'east': (sz, sy), 'west': (sz, sy), 'up': (sx, sz), 'down': (sx, sz)}
            for fc in FACES:
                if info['faces'] is not None and fc not in info['faces']:
                    continue
                fw, fh = dims[fc]
                if fw <= 0 or fh <= 0:
                    continue
                rects.append((i, fc, max(1, int(math.ceil(fw - 1e-6))), max(1, int(math.ceil(fh - 1e-6)))))
        # shelf pack, tallest first
        size = self.tex
        while True:
            placed = self._pack(rects, size)
            if placed is not None:
                break
            size *= 2
        self.tex = size
        img = np.zeros((size, size, 4), dtype=np.uint8)
        uvmap = {}
        for (i, fc, w, h), (x, y) in placed.items():
            bone, c, mat, info = self.cubes[i]
            frng = np.random.default_rng(rng.integers(1 << 30))
            face_img = mat.paint(w, h, fc, frng, info)
            gm = None
            if self.glow:
                gm = np.zeros((h, w), bool)
                for col in self.glow:
                    gm |= np.all(face_img == np.array(col, dtype=np.uint8), axis=-1)
                if getattr(mat, 'glow', False):
                    gm[:] = True
            if not getattr(mat, 'flat', False):
                face_img = bake_light(face_img, fc, gm)
            img[y:y + h, x:x + w, :3] = face_img
            img[y:y + h, x:x + w, 3] = 255
            if gm is not None:
                # entity_emissive_alpha: low alpha = self-lit (glows in the dark); the pixel is still drawn opaque
                img[y:y + h, x:x + w, 3][gm] = GLOW_ALPHA
            uvmap.setdefault(i, {})[fc] = {'uv': [x, y], 'uv_size': [w, h]}
        bones_out = []
        for b in self.bones:
            bb = dict(b)
            cubes = []
            for i, (bone, c, mat, info) in enumerate(self.cubes):
                if bone == b['name']:
                    cc = dict(c); cc['uv'] = uvmap.get(i, {})
                    cubes.append(cc)
            if cubes:
                bb['cubes'] = cubes
            bones_out.append(bb)
        bw, bh, bo = self.bounds
        geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
            'description': {'identifier': f'geometry.cookiedookie.{self.key}_creeper', 'texture_width': size,
                            'texture_height': size, 'visible_bounds_width': bw, 'visible_bounds_height': bh,
                            'visible_bounds_offset': [0, bo, 0]},
            'bones': bones_out}]}
        return geo, Image.fromarray(img, 'RGBA')

    @staticmethod
    def _pack(rects, size):
        order = sorted(rects, key=lambda r: (-r[3], -r[2]))
        x = y = shelf = 0
        out = {}
        for r in order:
            w, h = r[2], r[3]
            if w > size:
                return None
            if x + w > size:
                x = 0; y += shelf; shelf = 0
            if y + h > size:
                return None
            out[r] = (x, y)
            x += w; shelf = max(shelf, h)
        return out


# ------------------------------------------------------------------------------- base skeleton
def skeleton(m, head=None, body=None, legs=None, head_size=(8, 8, 8), body_size=(8, 12, 4), leg_size=(4, 6, 4),
             leg_spread=None, body_y=6, face=True):
    """Vanilla creeper rig (bone names/pivots match animation.creeper.legs)."""
    lx, ly, lz = leg_size
    bx, by, bz = body_size
    hx, hy, hz = head_size
    m.bone('body', [0, body_y, 0])
    m.bone('head', [0, body_y + by, 0], parent='body')
    spread = leg_spread or (lx / 2, bz / 2 + lz / 2)
    sx, sz = spread
    m.bone('leg0', [-sx, ly, sz]); m.bone('leg1', [sx, ly, sz])
    m.bone('leg2', [-sx, ly, -sz]); m.bone('leg3', [sx, ly, -sz])
    if body is not None:
        m.cube('body', [-bx / 2, body_y, -bz / 2], [bx, by, bz], body)
    if head is not None:
        m.cube('head', [-hx / 2, body_y + by, -hz / 2], [hx, hy, hz], head, face=face)
    if legs is not None:
        for name, px, pz in (('leg0', -sx, sz), ('leg1', sx, sz), ('leg2', -sx, -sz), ('leg3', sx, -sz)):
            m.cube(name, [px - lx / 2, 0, pz - lz / 2], [lx, ly, lz], legs, leg=name)
    return m


# ------------------------------------------------------------------------------- texture variants
def tint(img, mul=(1, 1, 1), add=(0, 0, 0)):
    a = np.array(img).astype(float)
    a[..., :3] = a[..., :3] * np.array(mul) + np.array(add)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def charge(img, seed=7, color=(150, 225, 255)):
    """Charged skin: brighter, with electric arcs crawling over every face."""
    a = np.array(img).astype(float)
    a[..., :3] = a[..., :3] * 0.85 + np.array([20, 35, 55])
    rng = random.Random(seed)
    h, w = a.shape[:2]
    alpha = a[..., 3] > 0
    emissive = bool(((a[..., 3] > 0) & (a[..., 3] < 255)).any())  # skin already has self-lit pixels
    for _ in range((w * h) // 90):
        x, y = rng.randrange(w), rng.randrange(h)
        for _ in range(rng.randint(3, 7)):
            if 0 <= x < w and 0 <= y < h and alpha[y, x]:
                a[y, x, :3] = color if rng.random() < .7 else (235, 250, 255)
                if emissive:
                    a[y, x, 3] = GLOW_ALPHA
            x += rng.choice([-1, 1]); y += rng.choice([-1, 0, 1])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
