# Creeper Spores — design protection registry

This registry adds the user's **November 23, 2026** 48,000-response protection report to the latest Creeper Spores GitHub source without changing game assets. It supplements earlier study/protection reports and their exact safeguards; it does not replace them.

## Read the decisions

```bash
python3 model_protection/inspect.py --verify
python3 model_protection/inspect.py --summary
python3 model_protection/inspect.py --creeper "Swamp" --feature "lily-pad"
python3 model_protection/inspect.py --question 1
python3 model_protection/inspect.py --export-nonexcluded protection_decisions.tsv
```

The compact report contains **all 600 named feature areas**, the original **80 question templates per feature**, and the 48,000 answer positions. It is losslessly reconstructible for every non-excluded question. An excluded position is not returned as a decision. The exact source archive was `report 5.46pm.zip`, and the SHA-256 of its decompressed UTF-8 report appears in `report_matrix.json`.

Do not treat the 15 candidate-version comparison questions as final selections, or a declined protection question as permission to edit. Every feature and condition is evaluated individually; prior scoped safeguards remain in force.

## Source protection and releases

The canonical editable addon in this repository is under `Creeper_Spores_0.8.30/source/`. Its most recent pre-registry main commit is `7f67c0125312e3a61a1e6b1079ca409c93cd56bc`.

Run `python3 model_protection/inspect.py --audit-changes origin/main` on a working branch to detect changes affecting the six guarded creeper assets. This is a **conservative file-level review gate**, not a claim that every subcomponent of every file is intrinsically protected. A file that mixes approved and protected parts requires human feature-level review. An explicit, specific approval must appear in `approved_changes.json` with a traceable approval reference; blanket/wildcard approvals are invalid.

A GitHub Actions check performs the registry integrity test and the guarded-file review on pull requests. Administrators must configure branch protection / required checks in GitHub if they want this process enforced against direct pushes; the files alone cannot prevent a maintainer from bypassing it.

**No model, texture, animation, behavior, spawn, recipe or pack file is changed by this update.** Minecraft runtime verification is a separate step.
