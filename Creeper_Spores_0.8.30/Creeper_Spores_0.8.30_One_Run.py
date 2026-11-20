"""Build installable Creeper Spores 0.8.30 packs using the adjacent full source ZIP."""
from pathlib import Path, PurePosixPath
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Creeper_Spores_0.8.30_Source_And_Offline_Tests.zip"
if not SOURCE.is_file():
    raise SystemExit("Put this builder beside Creeper_Spores_0.8.30_Source_And_Offline_Tests.zip, then run it again.")

def build_pack(source_zip: zipfile.ZipFile, folder: str, target: Path) -> None:
    prefix = folder.rstrip("/") + "/"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for info in sorted(source_zip.infolist(), key=lambda entry: entry.filename):
            name = info.filename
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix):]
            safe = PurePosixPath(relative)
            if safe.is_absolute() or ".." in safe.parts:
                raise ValueError(f"Unsafe source path: {name}")
            out.writestr(relative, source_zip.read(info))

with zipfile.ZipFile(SOURCE) as src:
    names = set(src.namelist())
    for required in ("behavior_pack/manifest.json", "resource_pack/manifest.json", "optional_worldgen_pack/manifest.json"):
        if required not in names:
            raise SystemExit(f"Incomplete source ZIP: missing {required}")
    behavior = HERE / "Creeper_Spores_0.8.30_Behavior.mcpack"
    resources = HERE / "Creeper_Spores_0.8.30_Resources.mcpack"
    optional = HERE / "Creeper_Spores_0.8.30_OPTIONAL_Native_Worldgen.mcpack"
    addon = HERE / "Creeper_Spores_0.8.30_Expanded.mcaddon"
    build_pack(src, "behavior_pack", behavior)
    build_pack(src, "resource_pack", resources)
    build_pack(src, "optional_worldgen_pack", optional)

with zipfile.ZipFile(addon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
    out.write(behavior, behavior.name)
    out.write(resources, resources.name)

for path in (behavior, resources, optional, addon):
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Corrupt package member {bad} in {path.name}")
print(f"Built validated 0.8.30 packs beside {SOURCE.name}")
