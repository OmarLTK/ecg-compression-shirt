# Errata: submitted report vs. arithmetic and internal consistency

The capstone report (*Wearable ECG with Real-Time Pathology Detection*, RP02, April 2026) is the source for this repository. Where its text disagrees with its own numbers, with itself, or with the arithmetic, the corrected value is used everywhere in this repo and the discrepancy is recorded here. Numeric items are reproduced by `analysis/design_checks.py`.

Confidence: **high** unless marked.

## A. Arithmetic

| # | Report says | Correct | Note |
|---|---|---|---|
| A1 | BLE test: expected samples = 360 Hz × 3 leads × **360 s** = 1,944,000 | × **1,800 s** (30 min) = 1,944,000 | The product is right; the stated duration is wrong (360 s gives 388,800). |
| A2 | Storage: a 30-min, 3-lead, 360 Hz recording is ≈ **3.9 M** samples | **1.944 M** samples | Off by 2×. The ≈ 15 MB JSON size should be re-measured, not rescaled. |
| A3 | BOM: SoftPulse dry electrodes, 5 × $36.00 = **$36.00** | **$180.00** | The printed $404.65 subtotal already assumes $180; summing the printed line totals gives $260.65. |
| A4 | BOM: 8-pin DIP socket, 10 × $0.27 = $2.73 | $2.70 | Rounding of unit price. Trivial. |
| A5 | Grand total $501.59 **CAD** | Mixed currency | $77.84 of SoftPulse freight, tariff, and tax is in **USD** and was added unconverted. |
| A6 | Regulator dissipates ≈ 600 mW "at 200 mA" | ≈ 330 mW at the measured 109 mA | 200 mA is not the system's measured draw anywhere in the report. |
| A7 | Iteration 2 bandpass: "0.47 µF / 10 kΩ **high-pass** input, 10 kΩ / 0.1 µF low-pass" | As written: HPF at **33.9 Hz**, LPF at 159 Hz | A 34 Hz high-pass removes most ECG energy. Either the values are swapped in the text or that iteration was mis-built. **Moderate** — needs the iteration-2 schematic. |
| A8 | Analysis section: LM358 output "measured **7 V**" | **7.68 V** (testing section) | Same measurement, two values. |

## B. Contradictions inside the report

| # | Statement | Conflicts with |
|---|---|---|
| B1 | Theory §1.3: RL electrode is a **driven right leg** | Conclusion: active right-leg drive is **future work**. The built circuit has a passive RL reference. |
| B2 | Abstract: "custom-designed, cost-effective **PCB**" | Iteration 4: build moved to **double-sided perfboard**; conclusion blames "noise coupling in the perfboard design". A layout figure exists; a fabricated PCB is not described. |
| B3 | BLE-vs-Wi-Fi table: ESP32 BLE ≈ **5 mA** avg → ≈ 100 h on 500 mAh | Power section: ESP32 draws ≈ **100 mA** streaming BLE → 4.6 h. The 5 mA figure assumes light sleep the firmware does not use. |
| B4 | Rendering "met 60 fps on **both platforms**" | Only an **iPhone 13** was tested. |
| B5 | Real-world classification: "**100 % accuracy** across all three runs" | No annotated ground truth; healthy subjects. Accuracy is undefined; an always-Normal classifier would score the same. |
| B6 | ML analysis: "**mild** overfitting", "strong performance", "reasonable generalization" | PAC F1 78 % → 6.8 % (val) → 7.5 % (test); PAC test recall 4.9 %. This is severe overfitting on the minority class. |
| B7 | Segmentation: windows of **36 samples** "capture a complete cardiac cycle" with P, QRS, T | 36 samples at 360 Hz = **100 ms** — roughly one QRS. A full P-to-T span is ≈ 600 ms (≈ 216 samples). Likely a typo (e.g. 360 or 256). **Moderate** — needs the training code. |
| B8 | Electrode theory: Ag/AgCl **with conductive gel** | Design objective: **dry** electrodes (SoftPulse) because gel irritates. The trade-off of dry contact (higher, less stable impedance) is not analysed. |
| B9 | "3-lead" acquisition | Circuit is **dual-lead** (two AD620 channels); Lead III must be derived. |
| B10 | Fig. 6: "12 leads Mason-Likar configuration" | The device uses 4 electrodes / 3 limb leads. |
| B11 | Bias divider powered from a "regulated **5 V** supply from the L7806CV", ESP32 fed "through its onboard **5 V** regulator" | L7806CV outputs 6 V; common ESP32 dev boards regulate VIN to **3.3 V**, not 5 V. The 5 V source for the divider is unexplained. **Moderate** — depends on the exact dev board. |
| B12 | BOM lists TC1262 (×3) and MCP3202 (×2) | TC1262 failed and was replaced; MCP3202 does not appear in the final signal chain (ESP32 internal ADC used). Fine as a spend record, but label them "not in final build". |

## C. Design issue not identified in the report

| # | Issue |
|---|---|
| C1 | *Applies only if the bias really is 2.5 V.* 2.5 V ± 0.3 V reaches 2.8 V; at 11 dB attenuation the ESP32 ADC is only recommended up to ≈ 2.45 V. The hand schematic and the layout both show **1.65 V from 3.3 V** (see F3); at that bias the swing is 1.35–1.95 V and this issue disappears. **Superseded:** the on-body scope capture sits around 1.45 V DC (G8), so the bias is 1.65 V and C1 does not apply. |
| C2 | HPF corner at 0.72 Hz is above the 0.5 Hz monitoring-ECG convention and far above the 0.05 Hz diagnostic convention; ST/T morphology is distorted. Acceptable for rhythm classification; should be stated as a scope limit. |

## D. Citations and references

| # | Issue |
|---|---|
| D1 | Two different references are both numbered **[45]** (Farahmand et al.; Health Canada SaMD guidance). |
| D2 | Text cites "**Clifford et al. [42]**"; reference [42] is **Behar et al.** (2013). |
| D3 | Numbering restarts: the Introduction's [1]–[7] (arrhythmia prevalence, market, physiology) resolve to the Theory section's sources — e.g. the "one in three" lifetime-risk claim points to [1], Nerbonne & Kass (2005), a review of ion channels. |
| D4 | Several web sources are blogs or vendor posts (Medium, company blogs, "I've shipped both") cited for performance numbers. Acceptable for engineering context, weak as evidence. |

## E. Editorial leftovers

- Template instructions still in the text: the TOC "Update Field" reminder; "You should demonstrate alternative design solutions…"; "Tabulate the cost of all materials…"; "Detail the obtained simulation results."
- Unresolved placeholders: "Table rtX", "Figures rfX–rfZ", "Table X2", "Table 4.1" (the stack table is Table 1).
- Wrong cross-references: confusion matrices are cited as Figures 12–14 and 13–14; they are Figures 16–18. Real-world results are cited as Figure 15; they are Figure 19.
- Duplicate section numbers: two sections numbered 2.1 under Alternative Designs.
- Typos: "eveng" → "event"; "to avoid head rotation" → presumably "to avoid rotation"; "Students A required" → "Student A required".

## F. Found in the source material (schematic, layout, photos, ML output, contribution summaries)

| # | Finding | Confidence |
|---|---|---|
| F1 | **In the logistic-regression baseline,** PAC was MIT-BIH symbol `a` (aberrated APC, 150 beats), not `A` (2,546 beats). The later ResNet pipeline fixed this (PAC = `A` + `a` = 2,696; see G1). Proven by the class supports and by the printed class weight (59,286 / (3 × 150) = 131.7467). See `ml/README.md`. | High |
| F2 | **The baseline's** validation and test sets contain zero PAC beats. The split is record-wise, and every `a` beat fell into training. PAC metrics on those sets are undefined, and the printed macro-F1 is meaningless for them. | High |
| F3 | Bias: the schematic and layout show 3.3 V → 1 MΩ / 1 MΩ → **1.65 V**. The report says 5 V → **2.5 V**. The DevKit's regulator outputs 3.3 V and the L7806CV outputs 6 V, so the report's "5 V" source is unexplained. | High that they conflict; 1.65 V more plausible |
| F4 | **No documented topology produces the claimed 0.72 Hz high-pass.** Report Fig. 13 confirms the series C → 1 kΩ topology (≈ 723 Hz). As drawn, 0.1 µF in series with the 1 kΩ inverting-input resistor gives ≈ 1.64 kHz (gain ≈ 0.06 at 1 Hz). The report's 0.22 µF version gives ≈ 723 Hz, or no high-pass at all if it is a shunt branch. The bench test passed 1 Hz at gain 100, so the board differs from both documents. | High (arithmetic); moderate (as-built) |
| F5 | The 10 kΩ / 0.47 µF "33.9 Hz low-pass" filters only if the output is taken at the capacitor node. The schematic and layout both tap the op-amp output. If built that way, there is no analog anti-alias filter. | Moderate |
| F6 | The firmware's "60 Hz notch" is a moving average. A 6-tap boxcar at 360 Hz nulls 60 Hz but is −3 dB at about 27 Hz, so it also low-passes the QRS. | Moderate (N = 6 inferred) |
| F7 | Model identity conflicts. The report says ResNet. Raphael's summary says logistic regression was selected over a CNN that underperformed. Tenzin's summary says the app shows CNN output. The appendix shows the ResNet was trained after the label fix and saved as `resnet1d_mitdb.keras`, so the ResNet results are real; which model the app called is still unconfirmed. | High that the accounts conflict |
| F8 | Casing location: the report says waist (Fig. 2); Justin's summary says upper arm with a Velcro strap. | High that they conflict |
| F9 | The 5 → 4 electrode reduction is justified as "the additional one wasn't included in the training dataset". MIT-BIH's second channel is modified V1 in most records. | High |
| F10 | The RL electrode and the 1N4148 clamps do not appear in the schematic or layout. Glass diodes are visible in the casing photo. | Moderate |
| F11 | The demo in the casing video runs the ESP32 from USB, not the 9 V cells. Fine for a demo; don't present it as battery operation. | High |

## G. Found in the report's own figures and appendix

| # | Finding | Confidence |
|---|---|---|
| G1 | ResNet pipeline: PAC = `A` + `a` (2,696). Record-wise split 33 / 7 / 8 with zero overlap, which is correct. **1,382 of the 1,684 test PACs come from record 232**, and the per-partition PAC counts match PhysioNet's per-record counts exactly (val 119, test 1,684). Test PAC recall of 4.9 % describes mostly one patient. | High |
| G2 | Beat window is **180 samples (500 ms)** per the appendix log, not the "36 samples" in the text (B7 resolved). | High |
| G3 | **The on-body recordings were sampled at 190 / 190 / 192 Hz** (Fig. 22 titles) but fed to the model as 360 Hz ("sample_index @ 360 Hz"). The "100 % accuracy" real-world result was produced on time-compressed input. | High |
| G4 | **The on-body inference picks signal polarity to maximize the mean P(Normal)** (`auto: max mean P(N)`; Subject Z flipped). This biases the reported outcome toward Normal. | High |
| G5 | The firmware's 190 → 360 Hz fix is claimed, but every recording in the report is at ≈ 190 Hz. Either the fix came after the recordings or it never landed. | High |
| G6 | Fig. 14 ("final circuit design") is not the built circuit. The LM358 panel is non-inverting, gain 11, with pin 8 tied to ground. The AD620 panel's input polarity is the reverse of the hand schematic. See `hardware/SCHEMATIC.md` §7. | High |
| G7 | The bench sine (Fig. 20) is ≈ 15 Hz, not 1 Hz, and shows the second stage alone (14 mVpp → 1.40 Vpp), not the 14 mV → 77 mV → 7.68 V chain described in the text. | Moderate-high (period read from the graticule) |
| G8 | The on-body scope capture (Fig. 21) shows **257 mVpp**, not ≈ 550 mVpp. It sits around 1.45 V DC, which supports a 1.65 V bias and rules out 2.5 V (F3). | Moderate-high |
| G9 | App screenshot (Fig. 12) shows "Signal Quality: Excellent" and "Signal too noisy for AI analysis" at the same time, "Optimal" next to "Abnormal Rhythm Detected", and a trace that is a wrapping ramp, not an ECG. It is a UI capture, not evidence of live classification. | High |
| G10 | Fig. 6 is captioned "12 leads Mason Likar", but it is a textbook 12-lead placement diagram and is likely copyrighted. It is not reproduced here. | Moderate |
| G11 | A right-leg-drive stage was designed in an early ±3.3 V iteration (appendix) and dropped. This explains the RLD claims in the theory section and on the CV, but RLD is not in the built device (B1). | High |
