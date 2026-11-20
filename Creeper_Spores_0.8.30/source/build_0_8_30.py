"""Build the Creeper Spores 0.8.30 Bedrock packs from this source folder."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build"
OUT.mkdir(parents=True, exist_ok=True)

def make_pack(folder: str, filename: str) -> Path:
    source = ROOT / folder
    target = OUT / filename
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for item in sorted(source.rglob("*")):
            if item.is_file():
                z.write(item, item.relative_to(source).as_posix())
    return target

behavior = make_pack("behavior_pack", "Creeper_Spores_0.8.30_Behavior.mcpack")
resources = make_pack("resource_pack", "Creeper_Spores_0.8.30_Resources.mcpack")
make_pack("optional_worldgen_pack", "Creeper_Spores_0.8.30_OPTIONAL_Native_Worldgen.mcpack")
addon = OUT / "Creeper_Spores_0.8.30_Expanded.mcaddon"
with zipfile.ZipFile(addon, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(behavior, behavior.name)
    z.write(resources, resources.name)
print(f"Built Bedrock packs in {OUT}")
