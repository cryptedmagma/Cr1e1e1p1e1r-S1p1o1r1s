"""Audit a finished Creeper Spores 0.8.31 release folder. Exit code 1 on any failure.

Run from (or point at) the folder holding the release files:
    python audit_release_0_8_31.py [release_folder]
Checks: every artifact present and intact; each .mcpack byte-matches its source folder (no missing or
stale members); the .mcaddon holds exactly the two core packs and they match the standalone ones; the
optional worldgen pack stays separate; manifest versions and dependency UUIDs link up; the
COMPLETE_EVERYTHING bundle holds byte-identical copies; and the offline test suite passes from a clean
extraction of the source ZIP. Writes Creeper_Spores_0.8.31_SHA256SUMS.txt on success.
Offline only: it cannot show that Minecraft accepts the packs.
"""
import hashlib, io, json, subprocess, sys, tempfile, zipfile
from pathlib import Path

V = "0.8.31"
VT = [0, 8, 31]
REL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
N = lambda part: REL / f"Creeper_Spores_{V}_{part}"
ARTIFACTS = ["Expanded.mcaddon", "Behavior.mcpack", "Resources.mcpack", "OPTIONAL_Native_Worldgen.mcpack",
             "Source_And_Offline_Tests.zip", "One_Run.py", "README.txt", "BEDROCK_TESTS.txt", "FULL_CHECKLIST.txt",
             "STATUS.txt", "VISUAL_RECORDS.txt", "BASELINE_LEDGER.txt", "Audit_Release.py", "COMPLETE_EVERYTHING.zip"]
failures = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)
    return cond


def zmembers(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        bad = z.testzip()
        check(bad is None, f"archive integrity (bad member: {bad})" if bad else "archive integrity")
        return {n: z.read(n) for n in z.namelist() if not n.endswith("/")}


print(f"Auditing {REL}")
for a in ARTIFACTS:
    check(N(a).is_file() and N(a).stat().st_size > 0, f"present: {N(a).name}")
if failures:
    sys.exit("Audit stopped: release files missing.")

src = zmembers(N("Source_And_Offline_Tests.zip").read_bytes())
folders = {"Behavior.mcpack": "behavior_pack/", "Resources.mcpack": "resource_pack/",
           "OPTIONAL_Native_Worldgen.mcpack": "optional_worldgen_pack/"}
packs = {}
for art, prefix in folders.items():
    got = zmembers(N(art).read_bytes()); packs[art] = got
    want = {k[len(prefix):]: v for k, v in src.items() if k.startswith(prefix)}
    check(set(got) == set(want), f"{art}: member list matches source {prefix} ({len(want)} files)"
          + (f" missing {sorted(set(want) - set(got))[:3]} stale {sorted(set(got) - set(want))[:3]}" if set(got) != set(want) else ""))
    check(all(got.get(k) == v for k, v in want.items()), f"{art}: every member byte-identical to source")
    man = json.loads(got["manifest.json"])
    check(man["header"]["version"] == VT, f"{art}: manifest version {man['header']['version']}")
    check(V in man["header"].get("description", "") or art.startswith("OPTIONAL"), f"{art}: manifest description names {V}")

bp, rp = (json.loads(packs[a]["manifest.json"]) for a in ("Behavior.mcpack", "Resources.mcpack"))
wg = json.loads(packs["OPTIONAL_Native_Worldgen.mcpack"]["manifest.json"])
dep = lambda m: {d.get("uuid"): d.get("version") for d in m.get("dependencies", []) if d.get("uuid")}
check(dep(bp).get(rp["header"]["uuid"]) == VT, "behavior pack depends on this resource pack version")
check(dep(rp).get(bp["header"]["uuid"]) == VT, "resource pack depends on this behavior pack version")
check(dep(wg).get(bp["header"]["uuid"]) == VT, "optional worldgen depends on this behavior pack version")
check(len({bp["header"]["uuid"], rp["header"]["uuid"], wg["header"]["uuid"]}) == 3, "three distinct pack UUIDs")

addon = zmembers(N("Expanded.mcaddon").read_bytes())
check(set(addon) == {N("Behavior.mcpack").name, N("Resources.mcpack").name}, ".mcaddon holds exactly the two core packs (worldgen stays separate)")
for art in ("Behavior.mcpack", "Resources.mcpack"):
    inner = addon.get(N(art).name)
    check(inner is not None and zmembers(inner) == packs[art], f".mcaddon copy of {art} matches the standalone pack")

everything = zmembers(N("COMPLETE_EVERYTHING.zip").read_bytes())
for a in ARTIFACTS[:-1]:
    hit = [k for k in everything if k.endswith("/" + N(a).name)]
    check(len(hit) == 1 and everything[hit[0]] == N(a).read_bytes(), f"COMPLETE_EVERYTHING holds an identical {N(a).name}")
for part, ws in (("README.txt", "0_8_31_README.txt"), ("BEDROCK_TESTS.txt", "0_8_31_BEDROCK_TESTS.txt"),
                 ("FULL_CHECKLIST.txt", "0_8_31_FULL_CHECKLIST.txt"), ("STATUS.txt", "0_8_31_STATUS.txt"),
                 ("VISUAL_RECORDS.txt", "0_8_31_VISUAL_RECORDS.txt"), ("BASELINE_LEDGER.txt", "0_8_31_BASELINE_LEDGER.txt"),
                 ("One_Run.py", "one_run_0_8_31.py"), ("Audit_Release.py", "audit_release_0_8_31.py")):
    check(src.get(ws) == N(part).read_bytes(), f"{N(part).name} matches the copy inside the source ZIP")

with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(N("Source_And_Offline_Tests.zip")) as z:
        z.extractall(tmp)
    r = subprocess.run([sys.executable, "test_0_8_31.py"], cwd=tmp, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    check(r.returncode == 0 and last.startswith("PASS"), f"offline suite from a clean extract: {last[:60]}")

if failures:
    print(f"\nAUDIT FAILED: {len(failures)} problem(s).")
    sys.exit(1)
sums = [f"{hashlib.sha256(N(a).read_bytes()).hexdigest()}  {N(a).name}" for a in ARTIFACTS]
N("SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
print(f"\nAUDIT PASSED. Wrote {N('SHA256SUMS.txt').name}. (Offline audit; Minecraft import not tested.)")
