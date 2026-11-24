"""Walking trails and orbiting particles for creeper variants (Bedrock client-side particles).

Each trail is a short one-shot emitter that a looping client animation fires every 0.15 s while the
creeper is walking (query.modified_move_speed). The emitter is in world space, so the particles stay
where they were dropped and form a trail. The Water Creeper's bubbles are a local-space emitter that
follows the creeper: they pop in around it, drift and fade. Everything here is cosmetic and client-only: no behavior,
spawning or gameplay changes.
"""
import json, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
RP = ROOT / 'resource_pack'
SPRITES = 'textures/particle/cs_trails'
FRAME = 8

# ------------------------------------------------------------------------------------------ sprites
# 8x8 pixel sprites along a strip, then two 16x16 lily pads. '.' is transparent.
ART = {
    1: ("........",   # glow mote
        "...yy...",
        "..yWWy..",
        ".yWWWWy.",
        ".yWWWWy.",
        "..yWWy..",
        "...yy...",
        "........"),
    2: ("...pp...",   # pink petal
        "..pPPp..",
        ".pPPPPp.",
        ".pPPPPp.",
        "..pPPp..",
        "..pPp...",
        "...p....",
        "........"),
    3: ("...ww...",   # white petal
        "..wVVw..",
        ".wVVVVw.",
        ".wVVVVw.",
        "..wVVw..",
        "..wVw...",
        "...w....",
        "........"),
    4: ("........",   # ember
        "...oo...",
        "..oYYo..",
        ".oYWWYo.",
        ".oYWWYo.",
        "..oYYo..",
        "...oo...",
        "........"),
    5: ("........",   # tiny toadstool
        "..rrrr..",
        ".rRwRRr.",
        ".rRRRwr.",
        "..ssss..",
        "...ss...",
        "...ss...",
        "........"),
    6: ("........",   # spore-queen puff
        "..mm.m..",
        ".mMMmMm.",
        ".MMPMMm.",
        ".mMMMMm.",
        "..mMMm..",
        "...mm...",
        "........"),
    7: ("..bbbb..",   # bubble (hollow ring with a highlight)
        ".b....b.",
        "b..W...b",
        "b.W....b",
        "b......b",
        "b......b",
        ".b....b.",
        "..bbbb.."),
}
COLORS = {
    'y': (150, 240, 80, 200), 'W': (240, 255, 220, 255),
    'p': (214, 104, 150, 255), 'P': (246, 160, 196, 255),
    'w': (210, 204, 190, 255), 'V': (255, 252, 244, 255),
    'o': (230, 90, 16, 220), 'Y': (255, 196, 64, 255),
    'r': (168, 30, 36, 255), 'R': (214, 58, 52, 255), 's': (232, 222, 206, 255),
    'm': (150, 80, 180, 220), 'M': (214, 120, 196, 255),
    'b': (170, 230, 255, 255),
}
FRAMES = {'glow': 0, 'petal_pink': 1, 'petal_white': 2, 'ember': 3, 'toadstool': 4, 'queen': 5, 'bubble': 6}
BIG = 16                         # lily pads are 16x16, packed after the 8x8 strip
SMALL_W = FRAME * len(ART)
PADS = {'lily_pad': SMALL_W, 'lily_pad_flower': SMALL_W + BIG}
SHEET_W, SHEET_H = SMALL_W + 2 * BIG, BIG


def lily_pad(flower):
    """Top-down 16x16 lily pad: round, a notch cut to the centre, radial veins, darker rim;
    optionally a pink water lily with a gold heart sitting on it."""
    import math
    img = Image.new('RGBA', (BIG, BIG), (0, 0, 0, 0))
    c, R = 7.5, 7.4
    for y in range(BIG):
        for x in range(BIG):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dy, dx)) % 360
            if d > R or (d > .8 and abs((ang - 300 + 180) % 360 - 180) < 13):
                continue
            col = (70, 160, 34)
            if d > R - 1.3:
                col = (44, 110, 20)
            elif d > 1.2 and (ang % 45 < 6 or ang % 45 > 39):
                col = (112, 196, 62)
            elif (x * 7 + y * 3) % 11 == 0:
                col = (84, 176, 42)
            img.putpixel((x, y), col + (255,))
    if flower:
        outer, inner, gold = (255, 196, 222, 255), (240, 120, 168, 255), (255, 206, 60, 255)
        fx, fy = 9, 9
        for ox in range(-3, 4):
            for oy in range(-3, 4):
                r = abs(ox) + abs(oy)
                if r <= 3 and not (abs(ox) == 3 and oy) and not (abs(oy) == 3 and ox):
                    img.putpixel((fx + ox, fy + oy), outer if r >= 2 else inner)
        img.putpixel((fx, fy), gold)
    return img


def write_sprites():
    img = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    for f, rows in enumerate(ART.values()):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    img.putpixel((f * FRAME + x, y), COLORS[ch])
    img.paste(lily_pad(False), (PADS['lily_pad'], 0))
    img.paste(lily_pad(True), (PADS['lily_pad_flower'], 0))
    out = RP / f'{SPRITES}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


# ------------------------------------------------------------------------------------------ particles
def uv(frame_expr, size=FRAME):
    return {"texture_width": SHEET_W, "texture_height": SHEET_H, "uv": [frame_expr, 0], "uv_size": [size, size]}


def fade(start=0.6):
    """Alpha stays full, then fades out over the last part of the particle's life."""
    return f"math.clamp((1 - variable.particle_age / variable.particle_lifetime) / {1 - start}, 0, 1)"


def trail_particle(ident, *, frame_expr, count, life, size, material="particles_alpha", rise=0.0, gravity=-1.2,
                   spread=0.3, lit=True, spin=False, height=0.05):
    comps = {
        "minecraft:emitter_rate_instant": {"num_particles": count},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_disc": {"offset": [0, height, 0], "radius": spread, "plane_normal": "y", "direction": "outwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": f"{life} + variable.particle_random_1 * {life * 0.4}"},
        "minecraft:particle_initial_speed": 0.15 if rise else 0.05,
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, rise if rise else gravity, 0], "linear_drag_coefficient": 3.0},
        "minecraft:particle_appearance_billboard": {
            "size": [f"{size} * (0.8 + variable.particle_random_2 * 0.4)", f"{size} * (0.8 + variable.particle_random_2 * 0.4)"],
            "facing_camera_mode": "rotate_xyz" if spin else "lookat_xyz",
            "uv": uv(frame_expr)},
        "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, fade()]},
    }
    if not rise:  # settle on the ground and stay put, making a visible trail
        comps["minecraft:particle_motion_collision"] = {"collision_radius": 0.04, "coefficient_of_restitution": 0, "collision_drag": 10}
    if spin:
        comps["minecraft:particle_initial_spin"] = {"rotation": "variable.particle_random_3 * 360", "rotation_rate": 0}
    if lit:
        comps["minecraft:particle_appearance_lighting"] = {}
    return {"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": ident, "basic_render_parameters": {"material": material, "texture": SPRITES}},
        "components": comps}}


def lily_trail(ident):
    """Lily pads left lying flat on the ground behind the Water Creeper; about one in three has a flower."""
    return {"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": ident, "basic_render_parameters": {"material": "particles_alpha", "texture": SPRITES}},
        "components": {
            "minecraft:emitter_rate_instant": {"num_particles": 1},
            "minecraft:emitter_lifetime_once": {"active_time": 0.05},
            "minecraft:emitter_shape_disc": {"offset": [0, "0.02 + variable.particle_random_4 * 0.02", 0], "radius": 0.3,
                                             "plane_normal": "y", "direction": "outwards"},
            "minecraft:particle_lifetime_expression": {"max_lifetime": "4.5 + variable.particle_random_1 * 1.5"},
            "minecraft:particle_initial_speed": 0,
            "minecraft:particle_initial_spin": {"rotation": "variable.particle_random_3 * 360", "rotation_rate": 0},
            "minecraft:particle_motion_dynamic": {},
            "minecraft:particle_appearance_billboard": {
                "size": ["0.22 + variable.particle_random_2 * 0.08", "0.22 + variable.particle_random_2 * 0.08"],
                "facing_camera_mode": "emitter_transform_xz",
                "uv": uv(f"variable.particle_random_2 < 0.33 ? {PADS['lily_pad_flower']} : {PADS['lily_pad']}", BIG)},
            "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, fade(0.75)]},
            "minecraft:particle_appearance_lighting": {},
        }}}


def bubble_particle(ident, frame):
    """Bubbles that pop into view around the creeper, drift slowly round it and fade away (about 4 at a time)."""
    grow = "math.min(variable.particle_age / 0.12, 1)"
    size = f"(0.07 + variable.particle_random_2 * 0.06) * {grow}"
    return {"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": ident, "basic_render_parameters": {"material": "particles_alpha", "texture": SPRITES}},
        "components": {
            "minecraft:emitter_local_space": {"position": True, "rotation": False},
            "minecraft:emitter_rate_steady": {"spawn_rate": 4, "max_particles": 4},
            "minecraft:emitter_lifetime_once": {"active_time": 1.0},
            "minecraft:emitter_shape_point": {},
            "minecraft:particle_lifetime_expression": {"max_lifetime": "0.9 + variable.particle_random_4 * 0.3"},
            "minecraft:particle_motion_parametric": {"relative_position": [
                "math.cos(variable.particle_random_1 * 360 + variable.particle_age * 50) * (0.6 + variable.particle_random_2 * 0.3)",
                "variable.particle_random_3 * 1.3 - 0.55 + variable.particle_age * 0.25",
                "math.sin(variable.particle_random_1 * 360 + variable.particle_age * 50) * (0.6 + variable.particle_random_2 * 0.3)"]},
            "minecraft:particle_appearance_billboard": {"size": [size, size], "facing_camera_mode": "lookat_xyz", "uv": uv(frame * FRAME)},
            # pop in, hold, then turn invisible
            "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, f"{grow} * {fade(0.55)}"]},
        }}}


F = lambda name: FRAMES[name] * FRAME
# key -> particle definitions (short name -> particle json); 'trail' plays while walking, 'orbit' always
EFFECTS = {
    'water': {
        'trail': lily_trail('cookiedookie:cs_trail_water'),
        'orbit': bubble_particle('cookiedookie:cs_orbit_bubbles', FRAMES['bubble']),
    },
    'glowing': {'trail': trail_particle('cookiedookie:cs_trail_glowing', frame_expr=F('glow'), count=3, life=1.4, size=0.12,
                                        material="particles_add", rise=0.25, lit=False, height=0.2)},
    'flower': {'trail': trail_particle('cookiedookie:cs_trail_flower',
                                       frame_expr=f"{F('petal_pink')} + math.floor(variable.particle_random_3 * 1.99) * {FRAME}",
                                       count=2, life=3.0, size=0.13, spin=True, gravity=-0.6, height=0.6)},
    'lava': {'trail': trail_particle('cookiedookie:cs_trail_lava', frame_expr=F('ember'), count=3, life=1.1, size=0.11,
                                     material="particles_add", rise=0.6, lit=False, height=0.1)},
    'mushroom': {'trail': trail_particle('cookiedookie:cs_trail_mushroom', frame_expr=F('toadstool'), count=1, life=3.5, size=0.2)},
    'spore_queen': {'trail': trail_particle('cookiedookie:cs_trail_spore_queen', frame_expr=F('queen'), count=3, life=2.6,
                                            size=0.16, gravity=-0.4, spread=0.5, height=0.3)},
}
TRAIL_LOCATOR = [0, 0.5, 0]   # model units: at ground level under the body
ORBIT_LOCATOR = [0, 14, 0]    # body centre

ANIMATIONS = {
    "format_version": "1.8.0",
    "animations": {
        # Re-fires every 0.15 s while the animation runs; the entity only runs it while walking.
        "animation.cookiedookie.walk_trail": {"loop": True, "animation_length": 0.15,
                                              "particle_effects": {"0.0": {"effect": "trail", "locator": "trail"}}},
        # A new 1 s orbit emitter each second keeps bubbles circling continuously.
        "animation.cookiedookie.orbit_particles": {"loop": True, "animation_length": 1.0,
                                                   "particle_effects": {"0.0": {"effect": "orbit", "locator": "orbit"}}},
    }}
WALK_QUERY = "query.modified_move_speed > 0.05"


def write_particles():
    write_sprites()
    for key, effects in EFFECTS.items():
        for kind, doc in effects.items():
            ident = doc['particle_effect']['description']['identifier'].split(':')[1]
            (RP / f'particles/{ident}.particle.json').write_text(json.dumps(doc, indent=2))
    (RP / 'animations/variant_trails.animation.json').write_text(json.dumps(ANIMATIONS, indent=2))


def wire(key):
    """Add locators to the geometry and particle/animation wiring to the client entity of one variant."""
    effects = EFFECTS.get(key, {})
    ent_path = RP / f'entity/{key}_creeper.entity.json'
    ent = json.loads(ent_path.read_text())
    d = ent['minecraft:client_entity']['description']
    # Always rebuild these entries from scratch so re-running is idempotent.
    d.pop('particle_effects', None)
    d['animations'] = {k: v for k, v in d['animations'].items() if k not in ('walk_trail', 'orbit_particles')}
    animate = [a for a in d['scripts']['animate'] if not (a == 'orbit_particles' or (isinstance(a, dict) and 'walk_trail' in a))]
    if effects:
        d['particle_effects'] = {kind: doc['particle_effect']['description']['identifier'] for kind, doc in effects.items()}
        if 'trail' in effects:
            d['animations']['walk_trail'] = 'animation.cookiedookie.walk_trail'
            animate.append({'walk_trail': WALK_QUERY})
        if 'orbit' in effects:
            d['animations']['orbit_particles'] = 'animation.cookiedookie.orbit_particles'
            animate.append('orbit_particles')
    d['scripts']['animate'] = animate
    ent_path.write_text(json.dumps(ent, indent=2))
    if effects:
        geo_path = RP / f'models/entity/{key}_creeper.geo.json'
        geo = json.loads(geo_path.read_text())
        body = next(b for b in geo['minecraft:geometry'][0]['bones'] if b['name'] == 'body')
        body['locators'] = {'trail': TRAIL_LOCATOR, 'orbit': ORBIT_LOCATOR}
        geo_path.write_text(json.dumps(geo, indent=1))


if __name__ == '__main__':
    write_particles()
    import designs
    for k in designs.DESIGNS:
        wire(k)
    print('particles:', sorted(p.name for p in (RP / 'particles').glob('cs_*.json')))
