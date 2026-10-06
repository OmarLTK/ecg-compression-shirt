# ecg-compression-shirt

A garment-integrated, three-lead wearable ECG that streams over Bluetooth Low Energy to a phone app and classifies each beat as Normal, PVC, or PAC. Biomedical Engineering capstone (RP02), Toronto Metropolitan University, 2026.

This repository is the engineering record of the build: the analog front-end and why it ended up the way it did, the five hardware iterations and what broke each one, the BLE and app pipeline, the classifier, the measured results, and the limits that were not solved. A script in [`analysis/`](analysis/design_checks.py) recomputes every design number from first principles; where the submitted report and the arithmetic disagree, [docs/ERRATA.md](docs/ERRATA.md) says so.

**Status:** working proof of concept on hand-wired perfboard. Not a medical device, not validated against annotated clinical recordings.

---

## What it does

Four electrodes (RA, LA, LL, RL) are held against the skin by a compression shirt. Two AD620 instrumentation-amplifier channels feed an LM358 gain stage, a passive band-limit, and a DC level shift into the ESP32's ADC at 360 Hz. The ESP32 streams the leads over BLE notifications to a React Native app that draws a 5-second scrolling trace at 60 fps, detects R-peaks, computes heart rate, SDNN, PR and QT, scores signal quality, and shows a per-beat label. The beat classifier is a dual-input 1D ResNet trained on the MIT-BIH Arrhythmia Database.

## Architecture

```
 Electrodes (RA, LA, LL; RL reference) in compression shirt
     │  47 kΩ series + 1N4148 clamps to ±9 V      (patient fault-current limit)
     ▼
 AD620  ×2  — G ≈ 5.9  (RG = 10 kΩ)              (low gain: survives electrode DC offset)
     ▼
 HPF 0.72 Hz (1 MΩ / 0.22 µF)
     ▼
 LM358 inverting — G = −100 (100 kΩ / 1 kΩ)      total |G| ≈ 594
     ▼
 LPF 33.9 Hz (10 kΩ / 0.47 µF)
     ▼
 10 µF AC coupling → 1 MΩ / 1 MΩ divider → 2.5 V bias   (one network per channel)
     ▼
 ESP32 ADC, 12-bit, 360 Hz  ─ 60 Hz digital notch ─ BLE GATT: 3 lead chars + 1 classification char
     ▼
 Phone app  (Expo SDK 54 · React Native 0.81 · react-native-ble-plx · Skia · Reanimated)
     ├─ base64 decode → circular buffer → Skia path on UI thread (60 fps)
     ├─ adaptive-threshold R-peak detector, 200 ms refractory → HR, SDNN, PR, QT
     ├─ pSQI signal-quality gate (score < 50 suppresses classification)
     └─ beat label: firmware classification if present, else on-device fallback

 Offline: 1D ResNet (waveform branch) + dense RR-interval branch → softmax {N, PVC, PAC}
          trained on MIT-BIH, class-weighted loss + PAC oversampling
```

Power: two 9 V alkaline batteries (±9 V rails), L7806CV feeding the ESP32 board, SPST switch on the positive rail so the circuit is fully de-energized while electrodes go on and off.

Full derivations: [docs/DESIGN.md](docs/DESIGN.md).

## Engineering log: what broke and what fixed it

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | AD620 output a flat line at −8 V with real electrodes; fine with a function generator | 50–80 mV half-cell offset between electrodes × gain 106 = 5.3–8.5 V of DC → saturation | Dropped AD620 gain to ≈ 6 (RG 470 Ω → 10 kΩ); moved the remaining gain after a high-pass that strips the offset |
| 2 | Clean trace on the scope, but recorded data was mostly noise | Total gain 60 put the ECG in < 1 % of the 0–3.3 V ADC span — under 4 effective bits | LM358 feedback 10 kΩ → 100 kΩ; total gain ≈ 600, ≈ 550 mVpp from real electrodes. SNR rose from ≈ 16 dB to ≈ 24 dB |
| 3 | 2.5 V bias node collapsed to 30 mV | LM358's low output impedance overpowered the 1 MΩ divider through a DC path | 10 µF series coupling capacitor; ECG now rides on the bias |
| 4 | Sharing one bias divider across channels | Each channel's AC signal would leak into the other through the shared node | Independent bias network per channel |
| 5 | TC1262 3.3 V regulator died moving from breadboard to perfboard | Regulator failure during the transition (cause not isolated) | L7806CV + 0.33 µF in / 0.1 µF ‖ 10 µF out; bias moved 1.65 V → 2.5 V |
| 6 | No protection between a fault and the patient | Inputs had series resistance only | 1N4148 clamps from each input to both rails behind the 47 kΩ resistors |
| 7 | Recorded heart rate and morphology looked wrong | ESP32 loop was oversampling and only delivering 190 Hz | Timestamped the pipeline, removed the oversampling, reached 360 Hz |
| 8 | Waveform dropped to 35–40 fps during classification bursts | BLE and ML state in one React context: every classification re-rendered the trace | Split into `BLEContext` / `MLContext` / `AuthContext`; 60 fps held |
| 9 | Trace unusable during walking or exercise | Motion artifact (≈ 1–10 Hz) overlaps the QRS band; dry electrodes shift on skin | **Not fixed.** SQI gate hides labels on bad segments; device is scoped to low-movement use |

## Results

| Measure | Result | Conditions |
|---|---|---|
| Analog gain (bench) | 5.5 (AD620) × 99.7 (LM358) | 14 mVpp, 1 Hz sine, function generator |
| ECG amplitude at LM358 out | ≈ 550 mVpp, PQRST visible | Gel electrodes, LA/RA/RL |
| Recording SNR | 15.8 → 23.8 dB after gain fix | 3 subject recordings |
| BLE packet loss | 0.00 % / 0.01 % / 0.12 % | 1 / 5 / 10 m, iPhone 13, 30-min sessions |
| BLE one-way latency | 5.2 / 5.8 / 7.1 ms | GPIO-toggle vs. callback timestamp |
| Decode fidelity (Pearson r) | ≥ 0.9993 | ESP32 serial log vs. phone-decoded samples |
| Render rate | 60 fps sustained | iPhone 13 |
| Classifier, test set | Macro-F1 64.4 %, balanced accuracy 66.0 % | MIT-BIH held-out split |
| — Normal | P 86.9 / R 96.0 / F1 91.2 % | |
| — PVC | P 92.1 / R 97.1 / F1 94.5 % | |
| — PAC | P 16.7 / R **4.9** / F1 7.5 % | |
| Battery life | ≈ 4.6 h (positive rail) | 109 mA draw, 500 mAh alkaline |

Detail and interpretation: [docs/RESULTS.md](docs/RESULTS.md).

## Known limitations

Stated plainly, because they are real.

- **PAC detection does not work.** Test recall is 4.9 %: the model labels almost every PAC as Normal. PAC F1 falls from 78 % on training data to under 8 % on validation and test, which is overfitting to a tiny minority class, not a mild generalization gap. PVC and Normal are the only classes with usable performance.
- **No clinical validation.** The three on-body recordings came from healthy subjects with no cardiologist annotation. Agreement with "expected physiology" there is not an accuracy figure; a model that always outputs Normal would pass it.
- **Motion kills the signal.** Medium and high activity make even R-peak detection unreliable. Use is limited to sitting, desk work, or sleep.
- **Battery life is hours, not days.** The ESP32 draws ≈ 100 mA while streaming, all of it through the positive 9 V cell. 72-hour Holter-style wear would need ~16 batteries; a separate Li-Po for the ESP32 is the fix.
- **ADC operating point is partly nonlinear.** The 2.5 V bias with ±0.3 V swing reaches 2.8 V, above the ≈ 2.45 V top of the ESP32 ADC's recommended linear range at 11 dB attenuation. Biasing near 1.3 V would keep the signal in the linear region.
- **No active right-leg drive.** RL is a passive reference. Common-mode rejection relies on the AD620 alone; the ≈ 6 dB SNR gap to clinical systems likely needs RLD and a ground-planed PCB.
- **Hand-wired perfboard.** A PCB layout exists; the tested unit is perfboard, with the noise coupling that implies.
- **Three leads from two amplifiers.** Two acquisition channels are measured; Lead III follows from Einthoven's law (III = II − I). No precordial lead, so bundle-branch morphology and PVC origin cannot be resolved.

## Repository layout

```
.
├── README.md
├── docs/
│   ├── DESIGN.md        # Signal chain derivations, BLE/app pipeline, classifier architecture
│   ├── RESULTS.md       # All measured results with conditions and interpretation
│   └── ERRATA.md        # Where the submitted report's text and the arithmetic disagree
├── analysis/
│   └── design_checks.py # Recomputes every design figure; prints PASS / FLAG
├── hardware/
│   ├── bom.csv          # Corrected bill of materials
│   └── README.md        # Where schematic, layout, and photos go
├── firmware/            # ESP32 acquisition + BLE  (pending upload)
├── app/                 # Expo / React Native app  (pending upload)
└── ml/                  # Training notebook, model, metrics  (pending upload)
```

Verify the numbers yourself:

```bash
python analysis/design_checks.py
```

## Team

Omar Ali-Yare, Justin Allen, Tenzin Dhonyoe, Raphael Mancini. Supervised by Robnier Reyes Perez, Department of Electrical, Computer & Biomedical Engineering, TMU.

<!-- TODO(Omar): replace with an accurate split before publishing, e.g.
**My role:** analog front-end design, five board iterations, bench validation, power and patient-safety protection.
Name only work you can defend line by line in an interview. -->

Source data for training: MIT-BIH Arrhythmia Database, PhysioNet (Moody & Mark, 2001; Goldberger et al., 2000).
