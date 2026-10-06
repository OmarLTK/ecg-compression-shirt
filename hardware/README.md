# Hardware

Owner: Omar Ali-Yare (Student A, analog front-end and acquisition). Wearable integration and casing by Justin Allen (Student C).

| File | What it is |
|---|---|
| [`SCHEMATIC.md`](SCHEMATIC.md) | Netlist, design review and photos. **Start here.** |
| `schematic_hand.jpg` | Final two-channel schematic (AD620 → LM358 → bias → ESP32) |
| `perfboard_layout_channel1.jpg` | Hand-drawn perfboard placement for channel 1 |
| `scope/` | Bench sine (gain 100), on-body ECG captures, the three ESP32 recordings |
| `iterations/` | Report Multisim figures (Fig. 13, 14) and earlier designs, including right-leg drive |
| `photos/` | Enclosure, top, side and ESP32/battery views |
| `video/` | Three short build walk-throughs (re-encoded to 720p) |
| `bom.csv` | Corrected bill of materials |

**BOM totals:** components CAD 404.62; DigiKey shipping and HST CAD 19.10; SoftPulse freight, tariff and tax **USD 77.84**. Convert the USD amount at the invoice date before quoting a single total. The `in_final_build` column marks parts that were bought but not used in the tested unit.

Still wanted:
- The Altium schematic and PCB source, plus a PDF export.
- A photo of the electrodes stitched into the shirt.
- The casing CAD or STL.
