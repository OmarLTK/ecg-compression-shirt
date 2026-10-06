# ecg-compression-shirt

A garment-integrated wearable ECG with two acquisition channels and three derived leads. It streams over Bluetooth Low Energy to a phone app that labels each beat as Normal, PVC or PAC. Biomedical Engineering capstone (RP02), Toronto Metropolitan University, 2026.

![Boards in the enclosure](hardware/photos/casing_open.jpg)

This repository is the engineering record of the build. It covers:
- the analog front-end and the five hardware iterations, including what broke each one;
- the hand-drawn schematic and layout, with a design review;
- the BLE and app pipeline;
- the classifier, including an audit of its training data;
- the measured results, and the limits that were not solved.

Two scripts recompute every number from first principles:
- [`analysis/design_checks.py`](analysis/design_checks.py) checks the hardware, link and BOM figures.
- [`analysis/ml_baseline_check.py`](analysis/ml_baseline_check.py) checks the classifier output.

Where the submitted report disagrees with the arithmetic or with the source material, [docs/ERRATA.md](docs/ERRATA.md) says so.

**Status:** working proof of concept, hand-soldered on perfboard. Not a medical device. Not validated against annotated clinical recordings.

---

## Architecture

```
 Electrodes RA, LA, LL (+ RL ground reference), dry Ag/AgCl, Mason–Likar torso sites, held by compression shirt
     │  47 kΩ series per input (fault current ≤ 191 µA)
     ▼
 AD620 ×2 — G = 5.94 (RG = 10 kΩ), REF = GND       ch1: RA − LA = −Lead I    ch2: RA − LL = −Lead II
     ▼                                              (low gain so electrode DC offset cannot saturate it)
 AC coupling → LM358 inverting, G = −100 (100 kΩ / 1 kΩ)   → +Lead I, +Lead II   total |G| ≈ 594
     ▼
 10 µF → 1 MΩ / 1 MΩ bias from 3.3 V → 1.65 V  (schematic; report says 2.5 V — see ERRATA F3)
     ▼
 ESP32-WROOM-32 DevKit — GPIO 34 / 35, 12-bit, 16× oversampled to 360 Hz,
                         moving-average 60 Hz null, digital baseline high-pass, Lead III = II − I
     ▼  BLE GATT: 3 lead characteristics + 1 classification characteristic
 Phone app — Expo SDK 54 · React Native 0.81 · react-native-ble-plx · Skia · Reanimated
     ├─ base64 decode → circular buffer → Skia path on UI thread (60 fps)
     ├─ adaptive-threshold R-peak detector, 200 ms refractory → HR, SDNN, PR, QT
     ├─ pSQI quality gate (score < 50 suppresses beat labels)
     └─ beat label {N, PVC, PAC}

 Offline: trained on the MIT-BIH Arrhythmia Database, record-wise split, class-weighted
```

Power: two 9 V alkaline cells (±9 V) mounted under the board stack, an L78xx regulator, and an SPST switch on the positive rail. The enclosure demo runs the ESP32 from USB.

Details:
- [docs/DESIGN.md](docs/DESIGN.md) — derivations.
- [hardware/SCHEMATIC.md](hardware/SCHEMATIC.md) — netlist, review and photos.
- [ml/README.md](ml/README.md) — classifier audit.
- [firmware/README.md](firmware/README.md) — acquisition firmware.

## Engineering log: what broke and what fixed it

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | AD620 output a flat line at −8 V with real electrodes; fine with a function generator | 50–80 mV half-cell offset between electrodes × gain 106 = 5.3–8.5 V of DC → saturation | AD620 gain dropped to ≈ 6 (RG 470 Ω → 10 kΩ); remaining gain moved after AC coupling |
| 2 | Clean trace on the scope, but recorded data was mostly noise | Total gain of 60 put the ECG in < 1 % of the ADC span (under 4 effective bits) | LM358 feedback 10 kΩ → 100 kΩ; total gain ≈ 600; SNR ≈ 16 dB → ≈ 24 dB |
| 3 | Bias node collapsed from mid-rail to 30 mV | The LM358's low output impedance overpowered the 1 MΩ divider through a DC path | 10 µF series coupling capacitor |
| 4 | Risk of crosstalk between leads | One shared bias divider would couple the two channels | Independent bias network per channel |
| 5 | TC1262 3.3 V regulator failed moving from breadboard to perfboard | Not isolated | L7806CV with 0.33 µF in and 0.1 µF ‖ 10 µF out |
| 6 | No protection between a fault and the patient | Series resistance only | 1N4148 clamps from each input to both rails, behind the 47 kΩ |
| 7 | Heart rate wrong; 60 Hz still present | Oversampling loop only reached 190 Hz, which also moved the moving-average null from 60 Hz to 31.7 Hz | Timestamped capture, loop fixed, 360 Hz restored |
| 8 | Waveform dropped to 35–40 fps during classification | BLE and ML state in one React context | Split contexts; 60 fps held |
| 9 | Trace unusable while walking or exercising | Motion artifact (≈ 1–10 Hz) overlaps the QRS band; dry electrodes shift on the skin | **Not fixed.** The SQI gate hides labels; use is scoped to low movement |

## Results

| Measure | Result | Conditions |
|---|---|---|
| Analog gain (bench) | 5.5 (AD620) × 99.7 (LM358) | 14 mVpp, 1 Hz sine |
| ECG amplitude at LM358 out | ≈ 550 mVpp, PQRST visible | Gel electrodes |
| Recording SNR | 15.8 → 23.8 dB after the gain fix | 3 subject recordings |
| BLE packet loss | 0.00 / 0.01 / 0.12 % | 1 / 5 / 10 m, iPhone 13, 30-min sessions |
| BLE one-way latency | 5.2 / 5.8 / 7.1 ms | GPIO toggle vs. callback timestamp |
| Decode fidelity (Pearson r) | ≥ 0.9993 | ESP32 serial log vs. phone |
| Render rate | 60 fps | iPhone 13 |
| Normal beats, test (baseline) | P 98.1 % / R 97.0 % | Logistic regression, record-wise split |
| PVC, test (baseline) | P 81.3 % / R 59.7 % | Same |
| PAC | **Not measurable** — see below | |
| Battery life | ≈ 4.6 h (+9 V cell) | 109 mA, 500 mAh alkaline |

Full tables: [docs/RESULTS.md](docs/RESULTS.md).

## Known limitations

- **PAC detection was never tested.** The pipeline labelled MIT-BIH `a` beats (150 aberrated APCs) as PAC and ignored the 2,546 ordinary `A` APCs. The record-wise split put all 150 in training, so the validation and test sets contain no PACs. The report's ResNet PAC numbers imply a different split that is not in this repository. See [ml/README.md](ml/README.md).
- **Which model shipped is unresolved.** The report describes a dual-input ResNet. The ML owner's summary says logistic regression was chosen because the CNN underperformed.
- **Analog filtering doesn't match the documentation.** As drawn, the input coupling gives a ≈ 1.6 kHz high-pass, and the low-pass RC hangs off the op-amp output, where it filters nothing. The working board must differ from the drawing. Analog band-limiting is unconfirmed; see [hardware/SCHEMATIC.md](hardware/SCHEMATIC.md).
- **The 60 Hz filter is a moving average.** It nulls 60 Hz but is −3 dB at about 27 Hz.
- **No clinical validation.** On-body recordings came from three healthy, unannotated subjects. Getting "mostly Normal" on them is not an accuracy figure.
- **Motion kills the signal.** Sitting, desk work and sleep only.
- **Battery life is hours.** The ESP32 draws about 100 mA through the +9 V cell. Multi-day wear needs a separate Li-Po and BLE light sleep.
- **No right-leg drive.** RL is a passive ground reference.
- **Frontal plane only.** Two acquired leads, Lead III derived, no V1. Bundle-branch morphology and PVC origin cannot be resolved.

## Repository layout

```
.
├── README.md
├── docs/
│   ├── DESIGN.md              # Derivations: lead system, AFE, power, BLE, app, classifier
│   ├── RESULTS.md             # Measured results with conditions
│   ├── ERRATA.md              # Report vs. arithmetic vs. source material
│   └── concept/               # Semester-1 block diagram (12-lead → 5-lead → final)
├── analysis/
│   ├── design_checks.py       # Hardware / link / BOM numbers → PASS / FLAG
│   └── ml_baseline_check.py   # Re-derives label mapping and split from confusion matrices
├── hardware/
│   ├── SCHEMATIC.md           # Netlist, design review, photo gallery
│   ├── schematic_hand.jpg
│   ├── perfboard_layout_channel1.jpg
│   ├── photos/  video/
│   └── bom.csv
├── firmware/README.md         # Acquisition behaviour (code pending)
├── app/README.md              # Phone app (code pending)
└── ml/
    ├── README.md              # Classifier audit
    └── baseline/              # Logistic-regression output screenshots
```

```bash
python analysis/design_checks.py
python analysis/ml_baseline_check.py
```

## Team

Supervised by Robnier Reyes Perez, Department of Electrical, Computer & Biomedical Engineering, TMU. Each member owned one subsystem; integration and testing were shared.

| Member | Owned |
|---|---|
| **Omar Ali-Yare** (A) | Analog front-end: requirements (360 Hz to match MIT-BIH), two-stage AD620/LM358 topology, the bias network, all five board iterations, breadboard-to-perfboard migration, the ESP32 sampling firmware (oversampling, 60 Hz rejection, baseline high-pass, the 190 → 360 Hz fix), and bench and on-body validation |
| Raphael Mancini (B) | ML pipeline: MIT-BIH preprocessing, beat-centred segmentation, logistic-regression baseline, 1D CNN; helped debug the AFE |
| Justin Allen (C) | Wearable: lead reduction, Mason–Likar placement, dry electrodes in the compression shirt, 3D-printed casing |
| Tenzin Dhonyoe (D) | Phone app and BLE pipeline: device discovery, packet handling, live display, end-to-end streaming tests |

Training data: MIT-BIH Arrhythmia Database, PhysioNet (Moody & Mark, 2001; Goldberger et al., 2000).

## License

Not yet chosen. All four authors need to agree on one before code is added.
