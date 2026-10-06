# Classifier

Owner: Raphael Mancini (Student B). MIT-BIH data is not redistributed here; download it from [PhysioNet](https://physionet.org/content/mitdb/1.0.0/).

## What is in this folder

`baseline/` holds terminal screenshots of the class-weighted **logistic-regression baseline** (`mitdb_windows.py`). There are two runs each of train, validation and test. [`analysis/ml_baseline_check.py`](../analysis/ml_baseline_check.py) transcribes the confusion matrices and re-derives everything below.

Still missing: the preprocessing and training code, the 1D CNN / ResNet code, the window length, and the model that actually ran in the app.

## What the baseline screenshots prove

### 1. "PAC" is MIT-BIH symbol `a`, not `A` — confidence: high

- Class supports across all splits total N 75,033 / V 7,129 / PAC **150**.
- MIT-BIH contains 75,052 N, 7,130 V, **2,546 `A`** (atrial premature beat) and **150 `a`** (aberrated atrial premature beat).
- The printed class weight 131.7467 equals 59,286 / (3 × 150) exactly.

So the pipeline trained "PAC" on 150 aberrated APCs and threw away the 2,546 ordinary APCs, the beats a PAC detector actually needs to find. An aberrated APC has a wide, PVC-like QRS, so the class it learned is close to the opposite of a typical PAC.

### 2. The split is by record, and val/test contain zero PACs — confidence: high

All 150 `a` beats are in training; validation and test have none. With a random per-beat split at these proportions, the chance of that is about 4 × 10⁻²². A record-wise (inter-patient) split is the right choice. The problem is that `a` beats come from very few records, so they all landed in one partition.

Consequences:
- PAC recall on val/test is **undefined**, not 0 %. Every PAC prediction there (231 on val, 401 on test, run 1) is a false positive.
- The printed val/test macro-F1 (≈ 0.55–0.62) averages in a class that is not in the split.
- On train, the 131× weight pushes about 3,900 Normal beats into PAC (PAC precision 3.2 %).

### 3. Baseline numbers that do mean something (run 1)

| Split | Normal P / R | PVC P / R |
|---|---|---|
| Validation | 98.0 / 97.0 % | 94.8 / 82.8 % |
| Test | 98.1 / 97.0 % | 81.3 / 59.7 % |

## Conflict with the report's ResNet results

The report's ResNet tables show **non-zero** PAC recall on validation (34.5 %) and test (4.9 %), so those runs had PACs in val and test. That means a different label mapping or split from this baseline. The ResNet numbers cannot be reproduced from anything in the repo yet.

The team's own accounts also disagree:
- Raphael's contribution summary says the 1D CNN *underperformed* logistic regression and that **logistic regression was selected**.
- The report presents a dual-input ResNet as the model.
- Tenzin's summary says the app displays "the CNN model that Raphael created".

Until the code is in this folder, treat the ResNet tables as unverified.

## What a fix looks like

1. Map PAC to `A` (optionally with `a`, `J`, `S`), or use the AAMI EC57 SVEB class (`A, a, J, S`), which is what published MIT-BIH work reports.
2. Use the de Chazal DS1/DS2 inter-patient record split (de Chazal et al., IEEE TBME 2004). It is the field-standard partition and keeps SVEB in both halves.
3. Add prematurity features (RR / local mean RR, next-RR / previous-RR). Most SVEB detection power comes from timing.
4. Report SVEB and VEB sensitivity and PPV, not macro-F1 alone.
