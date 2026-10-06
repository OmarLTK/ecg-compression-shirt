"""
Recompute every design figure quoted in the capstone report from first principles.

Run:  python analysis/design_checks.py
Each check prints the report's stated value, the recomputed value, and PASS / FLAG.
A FLAG means the report text and the arithmetic disagree; see docs/ERRATA.md.
"""

from math import pi

ROWS = []


def check(name, stated, computed, tol=0.03, unit=""):
    """Relative-tolerance comparison; stated=None means informational only."""
    if stated is None:
        status = "INFO"
    else:
        ok = abs(computed - stated) <= tol * max(abs(stated), 1e-12)
        status = "PASS" if ok else "FLAG"
    ROWS.append((status, name, stated, computed, unit))


# ---------------------------------------------------------------- analog front end
# AD620 gain: G = 1 + 49.4 kOhm / RG  (AD620 datasheet)
check("AD620 gain, RG = 470 ohm (iteration 1)", 106, 1 + 49.4e3 / 470)
check("AD620 gain, RG = 10 kohm (final)", 6, 1 + 49.4e3 / 10e3, tol=0.05)

# LM358 inverting stage: G = -Rf / Rin
check("LM358 gain, 100k / 1k (final)", 100, 100e3 / 1e3)
check("LM358 gain, 10k / 1k (iteration 2)", 10, 10e3 / 1e3)

g_total = (1 + 49.4e3 / 10e3) * 100
check("Total system gain (final)", 600, g_total, tol=0.02)

# Saturation from electrode DC offset in iteration 1 (50-80 mV half-cell mismatch)
for v_off in (0.050, 0.080):
    check(f"Iter-1 output from {v_off*1e3:.0f} mV DC offset (V)", None, v_off * 106, unit="V")

# RC corners: f = 1 / (2 pi R C)
f = lambda r, c: 1 / (2 * pi * r * c)
check("Report HPF RC product only, 1 Mohm x 0.22 uF (Hz) -- topology see FLAG below", 0.72, f(1e6, 0.22e-6), unit="Hz")
check("LPF RC, 10 kohm x 0.47 uF (Hz) -- filters only if tapped at cap node", 33.9, f(10e3, 0.47e-6), unit="Hz")
# Iteration 2 as written in the report: '0.47 uF / 10 kohm high-pass input'
check("Iter-2 'HPF' 10 kohm / 0.47 uF as written (Hz) -- would kill ECG", None, f(10e3, 0.47e-6), unit="Hz")
check("Iter-2 LPF 10 kohm / 0.1 uF (Hz)", None, f(10e3, 0.1e-6), unit="Hz")

# LM358 input coupling as drawn: 0.1 uF in series with 1 kohm to virtual ground (33 kohm shunt)
r_in = 1e3 * 33e3 / (1e3 + 33e3)
check("HPF as drawn, 0.1 uF into 1k||33k (Hz) -- report claims 0.72 Hz", 0.72, f(r_in, 0.1e-6), unit="Hz")
check("HPF per report values, 0.22 uF into 1 kohm (Hz)", 0.72, f(1e3, 0.22e-6), unit="Hz")
check("Suggested fix: 33 uF into 10 kohm, Rf 1 Mohm (Hz)", None, f(10e3, 33e-6), unit="Hz")

# Firmware moving-average 'notch': first null = fs / N
check("6-tap moving average null at 360 Hz (Hz)", 60, 360 / 6, unit="Hz")
check("Same filter at the buggy 190 Hz rate (Hz)", None, 190 / 6, unit="Hz")

# AC-coupling cap into the 1M||1M bias node: HPF corner
check("AC-coupling corner, 10 uF into 500 kohm (Hz)", None, f(0.5e6, 10e-6), unit="Hz")

# Bench test: 14 mV in -> 77 mV -> 7.68 V
check("Measured AD620 gain (77 mV / 14 mV)", 5.5, 77 / 14)
check("Measured LM358 gain (7.68 V / 77 mV)", 100, 7.68 / 0.077)

# Bias network -- report says 5 V -> 2.5 V; hand schematic and layout say 3.3 V -> 1.65 V
check("Bias midpoint per schematic, 3.3 V divider (V)", None, 3.3 * 0.5, unit="V")
check("Swing per schematic, 1.65 V +/- 0.3 V: top (V)", None, 1.65 + 0.3, unit="V")
v_bias = 5 * 1e6 / (1e6 + 1e6)
check("Bias midpoint (V)", 2.5, v_bias, unit="V")
check("Upper excursion with 600 mVpp (V)", 2.8, v_bias + 0.3, unit="V")
# ESP32 ADC1 at 11 dB attenuation: Espressif's recommended linear range tops out ~2.45 V
check("Headroom above ESP32 ~2.45 V linear limit (V, negative = in nonlinear region)",
      None, 2.45 - (v_bias + 0.3), unit="V")

# Patient fault current through 47 kohm input resistors from a 9 V rail
check("Worst-case input fault current (uA)", 200, 9 / 47e3 * 1e6, tol=0.10, unit="uA")

# Regulator dissipation (L7806CV, 9 V in, 6 V out)
check("L7806CV dissipation at report's 200 mA (W)", 0.6, 3 * 0.200, unit="W")
check("L7806CV dissipation at measured 109 mA (W)", None, 3 * 0.109, unit="W")

# ---------------------------------------------------------------- power
check("Positive 9 V battery life, 500 mAh / 109 mA (h)", 4.6, 500 / 109, unit="h")
check("Negative 9 V battery life, 500 mAh / 4 mA (h)", 125, 500 / 4, unit="h")
check("Positive batteries for 72 h", 15, 72 / (500 / 109), tol=0.10)
check("BLE-vs-WiFi table: 500 mAh / 5 mA (h)", 100, 500 / 5, unit="h")
check("Same table vs measured ESP32 ~100 mA streaming (h)", None, 500 / 100, unit="h")

# ---------------------------------------------------------------- BLE / storage
fs, leads, bytes_per = 360, 3, 2
bw = fs * leads * bytes_per
check("Payload bandwidth (B/s)", 2160, bw, unit="B/s")
check("Payload bandwidth (kbps)", 17.3, bw * 8 / 1e3, unit="kbps")
check("Headroom vs 37 kB/s BLE 4.2 DLE (x)", 17, 37e3 / bw, tol=0.05)

check("Samples in 30-min session (report's stated formula uses 360 s)",
      1_944_000, fs * leads * 360)
check("Samples in 30-min session (1,800 s)", 1_944_000, fs * leads * 1800)
check("Storage section: samples in 30-min recording", 3_900_000, fs * leads * 1800)
check("Max lost samples at 0.02 % of 30-min session", 400, 0.0002 * fs * leads * 1800, tol=0.05)

# ---------------------------------------------------------------- ML window
check("Beat window of 36 samples at 360 Hz (ms)", None, 36 / fs * 1e3, unit="ms")
check("Refractory 200 ms -> max HR (bpm)", 300, 60 / 0.200, unit="bpm")

# ---------------------------------------------------------------- BOM
bom = [  # (item, qty, unit_cad, line_total_as_printed)
    ("AD620", 2, 25.11, 50.22), ("LM358", 4, 0.42, 1.68), ("TC1262", 3, 1.73, 5.19),
    ("MCP3202", 2, 2.56, 5.12), ("8-pin DIP socket", 10, 0.27, 2.73),
    ("USB IDC motherboard cable", 1, 11.82, 11.82), ("Gel electrodes 12-pk", 1, 6.17, 6.17),
    ("5-pos header", 1, 0.39, 0.39), ("MyoWare reference cable", 10, 1.88, 18.80),
    ("USB IDC header cable", 1, 3.51, 3.51), ("Gel electrodes 12-pk", 2, 6.16, 12.32),
    ("SoftPulse dry electrodes", 5, 36.00, 36.00), ("SoftPulse flat", 5, 0.00, 0.00),
    ("Compression shirt", 2, 39.55, 79.10), ("ESP32 dev board", 1, 12.00, 12.00),
    ("L7806CV", 1, 1.50, 1.50), ("Perfboard", 3, 2.00, 6.00), ("47k", 6, 0.05, 0.30),
    ("10k", 4, 0.05, 0.20), ("1k", 2, 0.05, 0.10), ("100k", 2, 0.05, 0.10),
    ("1M", 4, 0.05, 0.20), ("33k", 2, 0.05, 0.10), ("0.1uF", 6, 0.10, 0.60),
    ("0.33uF", 1, 0.10, 0.10), ("0.47uF", 2, 0.10, 0.20), ("0.22uF", 2, 0.10, 0.20),
    ("10uF", 4, 0.15, 0.60), ("1N4148", 8, 0.05, 0.40), ("SPST switch", 1, 1.00, 1.00),
    ("Hookup wire", 1, 3.00, 3.00), ("Solder", 1, 0.00, 0.00), ("9V snaps", 2, 0.50, 1.00),
]
for item, q, u, printed in bom:
    if abs(q * u - printed) > 0.005:
        check(f"BOM line '{item}' qty x unit", printed, q * u, tol=0.001, unit="CAD")
check("BOM subtotal as printed vs sum of printed line totals", 404.65,
      sum(r[3] for r in bom), tol=0.001, unit="CAD")
check("BOM subtotal as printed vs sum of qty x unit", 404.65,
      sum(r[1] * r[2] for r in bom), tol=0.001, unit="CAD")
usd = 44.00 + 14.40 + 19.44
check("SoftPulse freight/tariff/tax, USD, added to CAD total unconverted", None, usd, unit="USD")


if __name__ == "__main__":
    w = max(len(r[1]) for r in ROWS)
    for status, name, stated, comp, unit in ROWS:
        s = "-" if stated is None else f"{stated:,.4g}"
        print(f"[{status}] {name:<{w}}  stated={s:>10}  computed={comp:,.4g} {unit}")
    flags = sum(r[0] == "FLAG" for r in ROWS)
    print(f"\n{flags} flag(s). See docs/ERRATA.md for the explanation of each.")
