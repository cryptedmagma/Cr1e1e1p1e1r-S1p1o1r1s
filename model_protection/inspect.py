#!/usr/bin/env python3
"""Inspect the scoped 48k-response Creeper Spores protection report; standard library only."""
import argparse
import base64
import collections
import csv
import json
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parent
CREEPERS = ("Swamp", "Crystal", "Jungle", "Lava", "Thorn", "Spore Queen")
STEMS = ("swamp", "crystal", "jungle", "lava", "thorn", "spore_queen")
EXPECTED = ((7065, 3), (8000, 0), (8000, 0), (8000, 0), (840, 4), (42, 1167))


def decoded(b64):
    return zlib.decompress(base64.b64decode(b64)).decode("utf-8")


def load():
    m = json.loads((ROOT / "report_matrix.json").read_text(encoding="utf-8"))
    features = json.loads(decoded(m["features_b64"]))
    templates = json.loads(decoded(m["question_templates_b64"]))
    statuses = decoded(m["answers_b64"])
    if (len(features), len(statuses), len(templates)) != (6, 48000, 80):
        raise ValueError("Matrix dimensions do not match the source report")
    if any(len(x) != 100 for x in features) or not set(statuses) <= set("YN."):
        raise ValueError("Invalid feature count or status")
    for c in range(6):
        chunk = statuses[c * 8000:(c + 1) * 8000]
        if (chunk.count("Y"), chunk.count("N")) != EXPECTED[c]:
            raise ValueError(f"Unexpected response counts for {CREEPERS[c]}")
    if len(set(f for xs in features for f in xs)) < 100:
        raise ValueError("Feature names missing")
    return m, features, templates, statuses


def decisions(features, templates, statuses):
    # Excluded positions are not yielded or considered decisions.
    for c, creeper in enumerate(CREEPERS):
        for f, feature in enumerate(features[c]):
            for q, template in enumerate(templates):
                question_no = c * 8000 + f * 80 + q + 1
                status = statuses[question_no - 1]
                if status == ".":
                    continue
                question = template.replace("{C}", creeper + " Creeper").replace("{F}", feature)
                yield question_no, creeper, feature, q + 1, question, ("Yes" if status == "Y" else "No")


def audit_changes(base_ref):
    """Flag six-creeper source edits for explicit human review: conservative file-level check."""
    repo = ROOT.parent
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only", f"{base_ref}...HEAD"],
            capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise RuntimeError(f"Git comparison failed: {e}")
    all_paths = [x.strip() for x in proc.stdout.splitlines() if x.strip()]
    src = "Creeper_Spores_0.8.30/source/"
    guarded = []
    for path in all_paths:
        if not path.startswith(src):
            continue
        suffix = path[len(src):]
        if any(stem + "_creeper" in suffix for stem in STEMS):
            guarded.append(path)
        elif suffix.startswith(("behavior_pack/", "resource_pack/")) and (
            "/animations/" in suffix or "/render_controllers/" in suffix or "/scripts/" in suffix
        ):
            # Shared motion and render-controller files may affect guarded models.
            guarded.append(path)
    approved = json.loads((ROOT / "approved_changes.json").read_text(encoding="utf-8"))
    rows = approved.get("approved_changes", [])
    missing = []
    for path in guarded:
        matches = [x for x in rows if x.get("path") == path
                   and x.get("status") == "approved"
                   and isinstance(x.get("component"), str) and x["component"].strip()
                   and isinstance(x.get("condition"), str) and x["condition"].strip()
                   and isinstance(x.get("approval_reference"), str)
                   and x["approval_reference"].strip()]
        if not matches:
            missing.append(path)
    if missing:
        print("Human review and exact feature-level approvals required before merging:")
        for x in missing:
            print(" -", x)
        return 2
    print(f"Guarded changed files: {len(guarded)}; each has a recorded exact-scope approval.")
    print("Warning: approval records are review documentation, not independently verified consent.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--summary", action="store_true")
    p.add_argument("--creeper")
    p.add_argument("--feature", help="Case-insensitive feature substring")
    p.add_argument("--question", type=int)
    p.add_argument("--export-nonexcluded", metavar="TSV_PATH")
    p.add_argument("--audit-changes", metavar="BASE_GIT_REF")
    a = p.parse_args()
    m, features, templates, statuses = load()
    if a.verify:
        print("PASS: 48,000 source positions, 600 features, 80 question templates, per-creeper response counts.")
        print("Source sha256:", m["source_sha256"])
    if a.summary or not any((a.verify, a.creeper, a.feature, a.question, a.export_nonexcluded, a.audit_changes)):
        for i, name in enumerate(CREEPERS):
            v = statuses[i * 8000:(i + 1) * 8000]
            print(f"{name:13} affirmative={v.count('Y'):5} declined={v.count('N'):5}; excluded positions not interpreted")
    if a.question is not None and not 1 <= a.question <= 48000:
        p.error("--question must be 1..48000")
    if a.creeper and a.creeper.lower() not in [x.lower() for x in CREEPERS]:
        p.error("--creeper must name one of the six creatures")
    if a.creeper or a.feature or a.question or a.export_nonexcluded:
        data = (r for r in decisions(features, templates, statuses)
                if (not a.creeper or r[1].lower() == a.creeper.lower())
                and (not a.feature or a.feature.lower() in r[2].lower())
                and (not a.question or r[0] == a.question))
        if a.export_nonexcluded:
            with open(a.export_nonexcluded, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, dialect="excel-tab")
                w.writerow(("question_id", "creeper", "feature", "question_offset", "question", "response"))
                w.writerows(data)
            print("Wrote scoped, non-excluded response table:", a.export_nonexcluded)
        else:
            for qid, _, _, _, question, answer in data:
                print(f"Q{qid}: {question}\nAnswer: {answer}\n")
    if a.audit_changes:
        return audit_changes(a.audit_changes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
