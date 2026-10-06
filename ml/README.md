# Classifier

Owner: Raphael Mancini (Student B). MIT-BIH data is not redistributed here; download it from [PhysioNet](https://physionet.org/content/mitdb/1.0.0/).

There are two pipelines in the evidence. The numbers in this file are reproduced by:
- [`analysis/ml_check.py`](../analysis/ml_check.py), from the confusion matrices.
- [`analysis/mitbih_label_audit.py`](../analysis/mitbih_label_audit.py), which checks per-record label counts against PhysioNet. It needs network access.

| | Logistic-regression baseline (`baseline/`) | ResNet-1D + RR (`resnet/`, report appendix) |
|---|---|---|
| PAC label | MIT-BIH `a` only (150 beats) | `A` + `a` (2,696 beats) |
| Split | Record-wise; all 150 PACs ended up in train | Record-wise: 33 / 7 / 8 records, overlap verified 0 |
| Beats | 82,312 | 84,858 (N 75,033 / V 7,129 / PAC 2,696) |
| Window | — | **180 samples = 500 ms** at 360 Hz (the report text says 36) |
| PAC decision | argmax | threshold τ = 0.23 on P(PAC), tuned on validation |

## 1. Baseline: PAC was never tested — confidence: high

- The class weight 131.7467 equals 59,286 / (3 × 150), so the PAC class was the 150 aberrated APCs (`a`).
- All 150 are in training. Validation and test contain zero PACs. The chance of that under a random per-beat split is about 4 × 10⁻²², so the split was record-wise and `a` beats come from very few records.
- PAC metrics on val/test are undefined; every PAC prediction there is a false positive.

Usable baseline results on test: Normal P 98.1 % / R 97.0 %, PVC P 81.3 % / R 59.7 %.

## 2. ResNet: the label fix was right, the test set is one patient's PACs — confidence: high

The ResNet pipeline corrected the label problem: PAC = `A` + `a`. The split is clean: no record appears in two partitions, which is correct and better than most student work on MIT-BIH.

| Split | Records | N | PVC | PAC |
|---|---|---|---|---|
| Train | 102 103 104 105 106 107 108 109 111 112 114 115 117 118 119 121 122 124 200 203 208 209 210 212 213 214 219 220 221 222 230 231 234 | 49,692 | 4,632 | 893 |
| Val | 100 101 113 116 123 215 223 | 14,923 | 750 | 119 |
| Test | 201 202 205 207 217 228 232 233 | 10,418 | 1,747 | 1,684 |

The PAC counts per partition match PhysioNet's per-record counts **exactly** (val 119, test 1,684). That match shows where the test PACs come from: **1,382 of the 1,684 (82 %) are from record 232**, a patient with sinus bradycardia and right bundle branch block. Consequences:

- **Test PAC recall of 4.9 % is mostly one patient.** The model called 1,464 of 1,684 test PACs Normal. Record 232's underlying beats are RBBB (`R`), which this pipeline excludes from the Normal class, so the model never saw that morphology as a baseline.
- **Validation had 119 PACs from 7 records**, 73 of them from record 223. The τ = 0.23 threshold was tuned on that and did not transfer.
- **The PVC result is sound.** Test PVC is P 92.1 % / R 97.1 % on 1,747 beats from 8 unseen patients.
- **The report's "mild overfitting" framing is wrong.** Training PAC is P 72 % / R 86 %, validation P 3.8 %, test R 4.9 %. That is a failure to generalize across patients.

**Better partition:** use the de Chazal DS1/DS2 split (de Chazal et al., IEEE TBME 2004). It is the field-standard inter-patient partition, it balances supraventricular ectopic beats (SVEB) across both halves, and it makes results comparable with published work. Report on the AAMI EC57 classes (N / SVEB / VEB / F / Q).

## 3. On-body "validation" does not validate anything — confidence: high

Three recordings were run through the ResNet (`resnet/inference_subject_*.png`). All 74 beats were classified Normal, and the report calls this "100 % accuracy". Three separate problems:

1. **Wrong sample rate.** The recordings were sampled at **190, 190 and 192 Hz** (Fs on each plot in `hardware/scope/recordings_subject_T_Z_Z2.png`). The inference script indexes them as 360 Hz. Each 180-sample window therefore spans about 940 ms instead of 500 ms, beats look 1.9× shorter than in training, and every RR feature is off by the same factor.
2. **Polarity chosen to make the answer Normal.** The log line `Beat-window polarity: +1 (auto: max mean P(N))` means the script tries both polarities and keeps the one the model scores as most Normal. Subject Z was flipped (−1). That selects for the Normal outcome by construction.
3. **No ground truth.** The subjects were healthy volunteers with no annotation. A classifier that always outputs Normal scores the same.

This also means the firmware's 190 → 360 Hz fix (`firmware/README.md`) had not been applied when these recordings were made. If 360 Hz was reached later, the on-body test needs re-recording.

## 4. Which model ran in the app

- The report and the appendix logs show a trained ResNet saved as `resnet1d_mitdb.keras`.
- Raphael's contribution summary says logistic regression was selected because the CNN underperformed. That may describe an earlier stage; the appendix shows the ResNet was trained after the label fix.
- The app screenshot shows rhythm labels ("Sinus Bradycardia") that neither model produces, so the app also has a rule-based HR classifier.

Confirm with Raphael and Tenzin which model the app actually called.

## Files

- `baseline/` — logistic-regression output, two runs per split.
- `resnet/step1_segmentation.png` … `step4_test.png` — the ResNet pipeline log.
- `resnet/confusion_*.png` — the ResNet confusion matrices.
- `resnet/inference_subject_*.png` — on-body inference logs.

Still wanted: `mitdb_windows.py`, the ResNet training script, and `resnet1d_mitdb.keras`.
