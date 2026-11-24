"""Build installable Creeper Spores 0.8.31 packs using the adjacent full source ZIP.

Non-overwriting: if a pack with the same name already exists and its contents differ from what this
source would produce, the build stops instead of replacing it. Pass --replace to overwrite deliberately.
Identical existing packs are left untouched.
"""
from pathlib import Path, PurePosixPath
import io, sys, zipfile

VERSION = "0.8.31"
HERE = Path(__file__).resolve().parent
SOURCE = HERE / f"Creeper_Spores_{VERSION}_Source_And_Offline_Tests.zip"
REPLACE = "--replace" in sys.argv[1:]
if not SOURCE.is_file():
    raise SystemExit(f"Put this builder beside {SOURCE.name}, then run it again.")


def pack_bytes(source_zip: zipfile.ZipFile, folder: str) -> bytes:
    prefix = folder.rstrip("/") + "/"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for info in sorted(source_zip.infolist(), key=lambda entry: entry.filename):
            name = info.filename
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix):]
            safe = PurePosixPath(relative)
            if safe.is_absolute() or ".." in safe.parts:
                raise ValueError(f"Unsafe source path: {name}")
            zi = zipfile.ZipInfo(relative, date_time=(2026, 11, 22, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(zi, source_zip.read(info))
    return buf.getvalue()


def members(data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n) for n in z.namelist()}


def write(target: Path, data: bytes) -> str:
    if target.exists():
        if members(target.read_bytes()) == members(data):
            return "unchanged"
        if not REPLACE:
            raise SystemExit(f"{target.name} already exists with different contents. Not overwriting it; "
                             f"move it aside or rerun with --replace.")
    target.write_bytes(data)
    return "written"


with zipfile.ZipFile(SOURCE) as src:
    names = set(src.namelist())
    for required in ("behavior_pack/manifest.json", "resource_pack/manifest.json", "optional_worldgen_pack/manifest.json"):
        if required not in names:
            raise SystemExit(f"Incomplete source ZIP: missing {required}")
    built = {
        HERE / f"Creeper_Spores_{VERSION}_Behavior.mcpack": pack_bytes(src, "behavior_pack"),
        HERE / f"Creeper_Spores_{VERSION}_Resources.mcpack": pack_bytes(src, "resource_pack"),
        HERE / f"Creeper_Spores_{VERSION}_OPTIONAL_Native_Worldgen.mcpack": pack_bytes(src, "optional_worldgen_pack"),
    }
behavior, resources = list(built)[:2]
addon_buf = io.BytesIO()
with zipfile.ZipFile(addon_buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
    for p in (behavior, resources):
        zi = zipfile.ZipInfo(p.name, date_time=(2026, 11, 22, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
        out.writestr(zi, built[p])
built[HERE / f"Creeper_Spores_{VERSION}_Expanded.mcaddon"] = addon_buf.getvalue()

for path, data in built.items():
    state = write(path, data)
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Corrupt package member {bad} in {path.name}")
    print(f"{state:9s} {path.name}")
print(f"Built validated {VERSION} packs beside {SOURCE.name}. Run audit_release_0_8_31.py next.")
