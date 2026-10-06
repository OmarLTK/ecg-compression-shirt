# Results

## 1. Analog front-end

**Bench gain.** 14 mVpp, 1 Hz sine from a function generator (−20 dB attenuator) at the AD620 inputs:

| Node | Amplitude | Stage gain |
|---|---|---|
| Input | 14 mV | — |
| AD620 out | 77 mV | 5.5 (theory 5.94) |
| LM358 out | 7.68 V | 99.7 (theory 100) |

Stage-1 shortfall of ≈ 7 % is within RG tolerance and AD620 gain error; not investigated further.

**On-body.** Gel electrodes at LA/RA/RL: ≈ 550 mVpp at the LM358 output with identifiable P, QRS, and T at 500 ms/div. Bias node held 2.5 V under load.

**Recordings and SNR.**

| Recording | Configuration | SNR | HR | R-peaks detected |
|---|---|---|---|---|
| Subject_T | Low gain | 16.7 dB | 71 bpm | 23 |
| Subject_Z | Low gain (early) | 15.8 dB | 75 bpm | 26 |
| Subject_Z2 | LM358 gain → 100 | 23.8 dB | 79 bpm | 26 |

Raising stage-2 gain so the signal fills more of the ADC span bought ≈ 8 dB. Clinical systems reach 30 dB or more; the remaining gap points at the perfboard (no ground plane), the passive RL reference, and the ADC operating point.

Sampling: R-R standard deviation under 50 ms at ≈ 75 bpm after the 190 Hz → 360 Hz fix.

## 2. BLE pipeline

30-minute continuous sessions (1,944,000 expected samples), iPhone 13:

| Distance | Packet loss | Mean one-way latency | Pearson r (sent vs. decoded) |
|---|---|---|---|
| 1 m | 0.00 % | 5.2 ms | 0.9997 |
| 5 m | 0.01 % | 5.8 ms | 0.9996 |
| 10 m | 0.12 % | 7.1 ms | 0.9993 |

At ≤ 5 m, worst case is under 400 lost samples per 30-minute session, and isolated single-sample gaps can be interpolated. End-to-end display delay is dominated by the 16.7 ms frame interval, not the radio.

Untested: Android, more than one phone model, interference-heavy environments, sessions longer than 30 minutes.

## 3. App rendering

60 fps sustained on iPhone 13 with live classification after splitting BLE and ML state into separate React contexts; 35–40 fps before. Android rendering was not measured.

## 4. Classifier (MIT-BIH)

### 4a. Logistic-regression baseline (verified from output screenshots)

Record-wise split, class-weighted. PAC = MIT-BIH `a` only (150 beats, all in train). Reproduced by `analysis/ml_baseline_check.py`.

| Split | Support N / V / PAC | Normal P / R | PVC P / R | PAC |
|---|---|---|---|---|
| Train | 54,089 / 5,047 / 150 | 99.5 / 85.1 % | 51.9 / 89.0 % | P 3.2 %, R 92.0 % |
| Validation | 8,632 / 1,109 / 0 | 98.0 / 97.0 % | 94.8 / 82.8 % | undefined (231 false positives) |
| Test | 12,312 / 973 / 0 | 98.1 / 97.0 % | 81.3 / 59.7 % | undefined (401 false positives) |

PVC recall drops from 83 % on validation to 60 % on test. With record-wise splits that is expected: PVC morphology is patient-specific, and the test records' PVCs differ from the training records'.

### 4b. ResNet-1D + RR, as reported (not reproducible from material in this repository)

These tables come from the submitted report. Their non-zero PAC recall on validation and test cannot come from the split above. Treat them as unverified until the training code is added.

Best run, selected on validation balanced accuracy.

**Per class (%)**

| Class | Train P / R / F1 | Validation P / R / F1 | Test P / R / F1 |
|---|---|---|---|
| Normal | 99.5 / 99.3 / 99.4 | 98.8 / 92.8 / 95.7 | 86.9 / 96.0 / 91.2 |
| PVC | 98.5 / 96.4 / 97.4 | 95.1 / 88.3 / 91.6 | 92.1 / 97.1 / 94.5 |
| PAC | 72.1 / 85.6 / 78.3 | 3.8 / 34.5 / 6.8 | 16.7 / 4.9 / 7.5 |

**Overall (%)**

| | Train | Validation | Test |
|---|---|---|---|
| Macro-F1 | 91.7 | 64.7 | 64.4 |
| Balanced accuracy | 93.8 | 71.8 | 66.0 |

### Interpretation

- **PVC and Normal generalize.** PVC F1 of 94.5 % on test is the strongest result in the project. Wide, early QRS complexes are easy morphology for a convolutional model.
- **PAC fails.** Recall of 4.9 % on test means 95 of every 100 PACs are called Normal. On validation, precision of 3.8 % means the tuned threshold fires mostly on Normal beats. The PAC threshold tuned on validation did not transfer to test, which is what you expect when the minority class has very few distinct source records.
- **This is overfitting, not a mild gap.** PAC F1 drops from 78 % to under 8 %; macro-F1 from 92 % to 64 %. Oversampling the minority class lets the network memorize the few PAC beats it has.
- **Normal precision of 86.9 % on test** is the mirror image: misclassified PACs (and some PVCs) land in Normal.

What would move PAC: a record-wise (inter-patient) split with PAC-bearing records in every partition, more PAC sources (INCART, the PhysioNet/CinC 2017 data, or the MIT-BIH Supraventricular database), explicit prematurity features (RR ratio to local mean), and reporting per AAMI EC57 classes (N / SVEB / VEB / F / Q) so results are comparable with published work.

## 5. On-body classification

The model was run on the three subject recordings above. All three subjects were healthy volunteers; no cardiologist annotation exists. Output was mostly Normal with few false PVCs, which is consistent with healthy physiology but **is not an accuracy measurement** — there is no ground truth, and a classifier that always outputs Normal would produce the same result. The submitted report's "100 % accuracy" for these runs should not be repeated.

## 6. Power

| Rail | Draw | Life on 500 mAh |
|---|---|---|
| +9 V | ≈ 109 mA | ≈ 4.6 h |
| −9 V | ≈ 4 mA | ≈ 125 h |

72 h of wear on the current design needs ≈ 16 positive-rail batteries. Moving the ESP32 onto its own Li-Po and enabling BLE light sleep between connection events are the two fixes.
