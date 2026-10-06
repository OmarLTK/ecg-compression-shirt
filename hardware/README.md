# Hardware

`bom.csv` is the corrected bill of materials: components CAD 404.62, DigiKey shipping and HST CAD 19.10, SoftPulse freight/tariff/tax **USD 77.84** (convert at the invoice date before quoting a single total). `in_final_build` marks parts that were bought but not used in the tested unit.

Pending upload (see the checklist in the top-level README):

- `schematic.pdf` — final AD620 + LM358 + bias + protection + ESP32 schematic (report Fig. 14)
- `layout/` — PCB layout source and a PDF/PNG export (report Fig. 15); say clearly that the tested unit is perfboard
- `iterations/` — schematics or annotated photos of iterations 1–4
- `photos/` — perfboard top/bottom, casing, shirt electrode mounting, scope captures (sine bench test, on-body PQRST)
- `casing/` — CAD source and STL for the waist enclosure (report Fig. 2–3)
