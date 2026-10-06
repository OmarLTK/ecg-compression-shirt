# Design

Every number in this file is reproduced by [`analysis/design_checks.py`](../analysis/design_checks.py).

## 1. Requirements

| Requirement | Target | Driven by |
|---|---|---|
| Rhythm content | Distinguish Normal, PVC, PAC beat by beat | PVC/PAC are intermittent; short clinic ECGs miss them |
| Electrodes | Dry, minimum count, held by garment | Hydrogel irritates on long wear; Holter wiring hurts compliance |
| Sample rate | 360 Hz, 12-bit | Matches MIT-BIH, so the trained model sees the same rate on-body |
| Link | Wireless, low power, no data loss | Long-term wear, phone as display |
| Display | 5-s scrolling trace at 60 fps | Usable live view |
| Safety | Bounded patient current, de-energize before electrode handling | Body-worn electrodes on a battery circuit |

## 2. Lead system

RA, LA, LL plus an RL reference give the three Einthoven limb leads:

- Lead I = V(LA) − V(RA)
- Lead II = V(LL) − V(RA)
- Lead III = V(LL) − V(LA), and I + III = II by Kirchhoff's voltage law

Two AD620 channels are acquired; the third lead is derived from the identity. Lead II sits near the normal P-wave axis (+45° to +60°), which makes it the most sensitive frontal lead for the abnormal P-waves of PACs. Torso placement works because limb leads are insensitive to position along the limb (Mason–Likar-style relocation), which is what lets the electrodes live inside a shirt.

What this cannot do: no transverse-plane lead (V1), so RBBB vs. LBBB morphology and left vs. right ventricular PVC origin are unresolvable. Fine for ectopic-beat detection and burden counting; insufficient for localization.

## 3. Analog front-end

### 3.1 Input protection
47 kΩ in series with each AD620 input, followed by 1N4148 diodes from the input to +9 V and from −9 V to the input. Worst-case current from a 9 V rail through 47 kΩ is 191 µA. The diodes are reverse-biased in normal operation and clamp the input to within one diode drop of the rails during a fault or ESD event; the 47 kΩ limits the clamp current. An SPST switch on the positive rail de-energizes everything before electrodes are attached.

### 3.2 Stage 1 — instrumentation amplifier
AD620, G = 1 + 49.4 kΩ / RG.

- RG = 470 Ω → G = 106 (iteration 1). Electrode half-cell mismatch of 50–80 mV became 5.3–8.5 V of DC: the output railed.
- RG = 10 kΩ → G = 5.94 (final). The DC offset now produces < 0.5 V, leaving headroom; measured 5.5.

Principle: keep pre-HPF gain low enough that worst-case electrode offset cannot saturate the stage; take the rest of the gain after the offset is removed.

### 3.3 Band-limit and Stage 2
- LM358 inverting: −100 kΩ / 1 kΩ = **−100** (measured 99.7). Because the stage inverts, the AD620 inputs are wired RA to +IN, which gives an upright Lead I and Lead II at the output.
- High-pass, as the report states it: 1 MΩ / 0.22 µF → 0.72 Hz. **That corner is not achievable in either documented topology.** As drawn (0.1 µF in series with the 1 kΩ input resistor), the corner is ≈ 1.64 kHz. See `hardware/SCHEMATIC.md` issue 1 and ERRATA F4.
- Low-pass: 10 kΩ / 0.47 µF → 33.9 Hz, but only if the output is taken at the capacitor node (issue 2).
- 60 Hz rejection in firmware: an N-sample moving average with N = 6 at 360 Hz nulls 60 Hz, but it is also a ≈ 27 Hz low-pass.

Total gain ≈ 594. A 1 mVpp ECG becomes ≈ 600 mVpp; ≈ 550 mVpp measured on real electrodes.

Trade-off: a 0.72 Hz corner is above the 0.05 Hz diagnostic-ECG convention and attenuates/distorts ST-segment and T-wave content. Acceptable for rhythm and beat-type detection, not for ST analysis. A 0.5 Hz corner (common for monitoring-grade ECG) would be the closer standard choice.

### 3.4 Level shift into the ADC
The ESP32 ADC accepts 0–3.3 V; the LM358 swings around 0 V on ±9 V rails.

- 10 µF series coupling capacitor blocks DC (the corner it forms with the 500 kΩ Thevenin bias impedance is 0.03 Hz, far below the 0.72 Hz HPF).
- 1 MΩ / 1 MΩ divider, one per channel. The schematic and layout feed it from **3.3 V → 1.65 V**; the report says 5 V → 2.5 V (ERRATA F3).
- At 1.65 V the ±0.3 V signal spans 1.35–1.95 V, inside the ESP32 ADC's linear range at 11 dB attenuation. At 2.5 V it would reach 2.8 V, above the ≈ 2.45 V recommended limit. Measuring the node settles which is true.

### 3.5 Power
| Rail | Load | Draw | 500 mAh alkaline lasts |
|---|---|---|---|
| +9 V | ESP32 (≈ 100 mA BLE streaming) via L7806CV, plus analog | ≈ 109 mA | ≈ 4.6 h |
| −9 V | AD620 ×2 (≈ 1.3 mA each), LM358 ×2 (≈ 0.7 mA each) | ≈ 4 mA | ≈ 125 h |

L7806CV dissipation is (9 − 6) V × 0.109 A ≈ 0.33 W at the measured draw. Running the ESP32 from its own Li-Po removes 105 mA from the 9 V cell and makes 72 h wear feasible on one pair of batteries.

## 4. Firmware and BLE

- Fixed 360 Hz sampling, verified by timestamping (an early build only reached 190 Hz).
- One GATT service, four notify characteristics: Lead I, Lead II, Lead III (12-bit samples packed in 16-bit words), and an 8-byte classification packet (label, confidence, sample index, instantaneous HR).
- Payload: 360 × 3 × 2 B = 2,160 B/s ≈ 17.3 kbps — about 1/17 of practical BLE 4.2 + DLE throughput (≈ 37 kB/s). Bandwidth is never the constraint; power is.
- Sequence numbers in packets let the app detect drops and reordering.

BLE was chosen over Wi-Fi on power: the ESP32 draws on the order of 95–240 mA with Wi-Fi active. Note that the measured BLE streaming draw (≈ 100 mA) is also far above the ≈ 5 mA light-sleep figure from the literature: the firmware never enters light sleep between connection events. That is the largest remaining power optimization.

## 5. Phone app

| Layer | Choice |
|---|---|
| Framework | Expo SDK 54, React Native 0.81, React 19 |
| BLE | react-native-ble-plx 3.5 |
| Rendering | @shopify/react-native-skia |
| Animation / UI-thread work | react-native-reanimated 4 |
| Navigation | expo-router |
| Storage | AsyncStorage (metadata) + expo-file-system (raw samples, JSON) |

Design decisions:

- **Skia canvas over SVG.** A 5 s window at 360 Hz is 1,800 points per lead; one SVG node per segment stutters. Skia draws in immediate mode to a GPU buffer.
- **Path built on the UI thread.** A Reanimated `useDerivedValue` worklet reads the circular buffer and builds the Skia path, so JS-thread work (classification) cannot stall the trace.
- **Separated contexts.** BLE updates arrive every 20–50 ms; keeping ML state in a different context stopped classification from re-rendering the waveform (35–40 fps → 60 fps).
- **R-peak detection.** Threshold = mean + 0.5 × (max − mean) over a sliding window, 200 ms refractory (caps detection at 300 bpm). Runs on a 500 ms timer via `InteractionManager.runAfterInteractions()`. Simpler than full Pan–Tompkins, no learning phase.
- **Signal-quality gate.** pSQI = power(5–15 Hz) / power(5–40 Hz), mapped to 0–100. Below 50 the app keeps drawing the trace and HR but suppresses beat labels and warns the user.
- **Fully offline.** Mock authentication, no backend; scope was the ECG pipeline.

Storage note: a 30-minute three-lead session is 1.944 M samples. JSON was chosen for debuggability; a binary format would cut size several-fold.

## 6. Classifier

- **Task:** supervised, three classes — Normal (N), PVC, PAC.
- **Data:** MIT-BIH Arrhythmia Database (360 Hz), beat windows centred on annotated R-peaks, plus RR-interval features. Labels: N, V and `a`.
- **Baseline:** class-weighted logistic regression (Raphael's summary says this was the model selected).
- **Architecture:** dual-input. Branch 1: 1D convolutional residual blocks on the waveform (depth up, temporal resolution down). Branch 2: fully connected layers on RR features. Concatenate → dense layers with dropout → softmax.
- **Why the RR branch:** PACs often look morphologically normal; prematurity is the defining feature.
- **Imbalance handling:** class-weighted categorical cross-entropy plus PAC oversampling; Adam optimizer.
- **Protocol:** fixed-seed train / validation / test split; multiple seeds; model selected on validation balanced accuracy; post-training PAC threshold tuning on validation; single evaluation on test.
- **Rejected alternative:** logistic regression on hand-built features — cheap and interpretable but linear, and PAC needs subtle combined shape-and-timing cues.

Settled from the baseline output (ERRATA F1–F2): the split is by record, and "PAC" was MIT-BIH `a` (150 aberrated APCs), not `A` (2,546 APCs). Still open: the true window length, and whether the ResNet used the same split and labels.
