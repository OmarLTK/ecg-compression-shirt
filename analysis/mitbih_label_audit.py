"""
Count beat labels per MIT-BIH record and per split, to verify the tables in ml/README.md.

    pip install wfdb
    python analysis/mitbih_label_audit.py            # downloads annotations from PhysioNet

Not run in this repository's CI: it needs network access to physionet.org.
"""
from collections import Counter
import wfdb

SPLITS = {
    "val":  ["100", "101", "113", "116", "123", "215", "223"],
    "test": ["201", "202", "205", "207", "217", "228", "232", "233"],
}
KEEP = {"N", "V", "A", "a"}

for split, recs in SPLITS.items():
    total = Counter()
    for r in recs:
        ann = wfdb.rdann(r, "atr", pn_dir="mitdb")
        c = Counter(s for s in ann.symbol if s in KEEP)
        total += c
        print(f"{split:<5} {r}: " + "  ".join(f"{k}={c.get(k, 0)}" for k in ("N", "V", "A", "a")))
    print(f"{split:<5} TOTAL: N={total['N']} V={total['V']} A+a={total['A'] + total['a']}\n")
