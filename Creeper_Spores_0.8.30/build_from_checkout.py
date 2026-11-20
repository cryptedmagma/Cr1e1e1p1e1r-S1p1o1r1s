#!/usr/bin/env python3
"""Validate and build Bedrock packs from the live checkout, not the archived ZIP.

One run: python Creeper_Spores_0.8.30/build_from_checkout.py
No prompts, network or third-party dependencies.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
RP = SRC / "resource_pack"
BP = SRC / "behavior_pack"
OPTIONAL = SRC / "optional_worldgen_pack"
OUT = ROOT / "dist"
NAMES = (
    "moss", "cave", "crystal", "swamp", "desert", "snow", "jungle",
    "mushroom", "sculk", "nether", "end", "water", "lava", "flower",
    "thorn", "phantom", "giant", "miniature", "glowing", "spore_queen",
    "grass_crown", "carved_wood", "slender_green",
)

def load(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"Missing source file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))

def validate() -> None:
    bp = load(BP / "manifest.json")
    rp = load(RP / "manifest.json")
    bph, rph = bp["header"], rp["header"]
    if not any(d.get("uuid") == rph["uuid"] and d.get("version") == rph["version"]
               for d in bp["dependencies"]):
        raise ValueError("Behavior pack must depend on the matching resource pack")
    if not any(d.get("uuid") == bph["uuid"] and d.get("version") == bph["version"]
               for d in rp["dependencies"]):
        raise ValueError("Resource pack must depend on the matching behavior pack")
    for name in NAMES:
        stem = name + "_creeper"
        eid = "cookiedookie:" + stem
        behavior = load(BP / "entities" / (stem + ".json"))
        client = load(RP / "entity" / (stem + ".entity.json"))
        model = load(RP / "models" / "entity" / (stem + ".geo.json"))
        if behavior["minecraft:entity"]["description"]["identifier"] != eid:
            raise ValueError(f"Behavior identifier mismatch: {stem}")
        desc = client["minecraft:client_entity"]["description"]
        if desc["identifier"] != eid:
            raise ValueError(f"Client identifier mismatch: {stem}")
        geometries = model.get("minecraft:geometry", [])
        if len(geometries) != 1:
            raise ValueError(f"Expected exactly one geometry: {stem}")
        geo = geometries[0]
        if desc["geometry"]["default"] != geo["description"]["identifier"]:
            raise ValueError(f"Geometry identifier mismatch: {stem}")
        if not desc.get("render_controllers"):
            raise ValueError(f"Missing render controller: {stem}")
        for skin in ("default", "charged", "alt", "alt_charged"):
            path = RP / (desc["textures"][skin] + ".png")
            if not path.is_file() or path.stat().st_size < 100:
                raise ValueError(f"Missing skin: {stem}/{skin}")
        wd = geo["description"]["texture_width"]
        ht = geo["description"]["texture_height"]
        bones = geo["bones"]
        names = {bone["name"] for bone in bones}
        if not {"head", "body", "leg0", "leg1", "leg2", "leg3"}.issubset(names):
            raise ValueError(f"Missing standard animated bones: {stem}")
        if len(names) != len(bones):
            raise ValueError(f"Duplicate bone: {stem}")
        for bone in bones:
            if not bone.get("cubes"):
                raise ValueError(f"Empty bone: {stem}/{bone['name']}")
            for cube in bone["cubes"]:
                if len(cube["size"]) != 3 or any(s <= 0 or not math.isfinite(s) for s in cube["size"]):
                    raise ValueError(f"Invalid cube size: {stem}")
                if len(cube["origin"]) != 3 or any(not math.isfinite(v) for v in cube["origin"]):
                    raise ValueError(f"Invalid cube origin: {stem}")
                if "rotation" in cube and ("pivot" not in cube or any(abs(x) > 45 for x in cube["rotation"])):
                    raise ValueError(f"Invalid cube rotation: {stem}")
                uv = cube.get("uv")
                if isinstance(uv, dict):
                    for face in uv.values():
                        u, v = face["uv"]
                        su, sv = face["uv_size"]
                        if min(u, v) < 0 or u + abs(su) > wd or v + abs(sv) > ht:
                            raise ValueError(f"UV outside atlas: {stem}")
                elif not isinstance(uv, list):
                    raise ValueError(f"Missing cube UV: {stem}")
    print(f"Validated geometry, materials and 4 skins each for {len(NAMES)} Creepers")

def zip_folder(source: Path, dest: Path) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(source.rglob("*")):
            if path.is_file() and not path.name.startswith(".") and "__pycache__" not in path.parts:
                z.write(path, path.relative_to(source).as_posix())
    with zipfile.ZipFile(dest) as z:
        bad = z.testzip()
        if bad or "manifest.json" not in z.namelist():
            raise ValueError(f"Invalid pack archive {dest.name}: {bad}")

def build() -> None:
    validate()
    OUT.mkdir(parents=True, exist_ok=True)
    behavior = OUT / "Creeper_Spores_Visual_Refined_Behavior.mcpack"
    resources = OUT / "Creeper_Spores_Visual_Refined_Resources.mcpack"
    addon = OUT / "Creeper_Spores_Visual_Refined.mcaddon"
    zip_folder(BP, behavior)
    zip_folder(RP, resources)
    with zipfile.ZipFile(addon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(behavior, behavior.name)
        z.write(resources, resources.name)
    with zipfile.ZipFile(addon) as z:
        if z.testzip() or len(z.namelist()) != 2:
            raise ValueError("Invalid combined add-on")
    if OPTIONAL.is_dir() and (OPTIONAL / "manifest.json").is_file():
        zip_folder(OPTIONAL, OUT / "Creeper_Spores_OPTIONAL_Native_Worldgen.mcpack")
    print(f"Installable Bedrock file: {addon}")

if __name__ == "__main__":
    build()
