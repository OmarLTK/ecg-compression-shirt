"""
Re-derive what the logistic-regression baseline screenshots (ml/baseline/*.png) imply
about the dataset, the label mapping, and the split.

Run:  python analysis/ml_check.py

Confusion matrices are transcribed from the screenshots. Rows = actual, cols = predicted,
order = [N, V, a]. 'a' is the label the pipeline used for PAC.
"""

CM = {
    "train_run1": [[46044, 4159, 3886], [213, 4492, 342], [8, 4, 138]],
    "train_run2": [[46364, 4210, 3515], [235, 4542, 270], [5, 3, 142]],
    "val_run1":   [[8373, 50, 209], [169, 918, 22], [0, 0, 0]],
    "val_run2":   [[8391, 41, 200], [175, 911, 23], [0, 0, 0]],
    "test_run1":  [[11941, 134, 237], [228, 581, 164], [0, 0, 0]],
    "test_run2":  [[11855, 181, 276], [303, 588, 82], [0, 0, 0]],
}
CLASSES = ["N", "V", "a"]
PRINTED_WEIGHTS = {0: 0.3653607942465196, 1: 3.9155934218347532, 2: 131.74666666666667}

# Beat counts in the full MIT-BIH Arrhythmia Database (PhysioNet annotation summary).
MITBIH = {"N": 75052, "V": 7130, "A (atrial premature)": 2546, "a (aberrated APC)": 150}


def support(cm):
    return [sum(r) for r in cm]


def metrics(cm):
    out = []
    for i in range(3):
        tp = cm[i][i]
        col = sum(cm[r][i] for r in range(3))
        row = sum(cm[i])
        p = tp / col if col else 0.0
        r = tp / row if row else float("nan")
        out.append((p, r))
    return out


print("Support per split (N, V, a):")
for k in ("train_run1", "val_run1", "test_run1"):
    print(f"  {k:<11} {support(CM[k])}")
tot = [sum(support(CM[k])[i] for k in ("train_run1", "val_run1", "test_run1")) for i in range(3)]
print(f"  total       {tot}   vs MIT-BIH N={MITBIH['N']}, V={MITBIH['V']}, "
      f"a={MITBIH['a (aberrated APC)']}, A={MITBIH['A (atrial premature)']}")

# 1. Which annotation symbol is 'PAC'?  Class weight = n_total / (n_classes * n_class)
n_train = sum(support(CM["train_run1"]))
n_a = support(CM["train_run1"])[2]
print(f"\nTrain size {n_train}, PAC support {n_a}")
print(f"Weight implied for PAC = {n_train / (3 * n_a):.4f}  (printed {PRINTED_WEIGHTS[2]:.4f})")
print("=> PAC = MIT-BIH symbol 'a' only (150 beats). The 2,546 'A' beats were not used.")

# 2. Was the split by record or by beat?
f_test = sum(support(CM["test_run1"])) / sum(tot)
f_val = sum(support(CM["val_run1"])) / sum(tot)
p_zero = (1 - f_test - f_val) ** 150
print(f"\nTest fraction {f_test:.3f}, val fraction {f_val:.3f}")
print(f"P(all 150 'a' beats land in train | random per-beat split) = {p_zero:.2e}")
print("=> Split is by record. Every 'a' beat is in train; val and test contain zero PACs.")

# 3. What the PAC metrics mean
print("\nPer-class precision / recall:")
for k, cm in CM.items():
    m = metrics(cm)
    pred_a = sum(cm[r][2] for r in range(3))
    print(f"  {k:<11} " + "  ".join(f"{c}: P={p:6.1%} R={r:6.1%}" for c, (p, r) in zip(CLASSES, m))
          + f"   predicted-as-PAC={pred_a}")
print("\nOn val/test every PAC prediction is a false positive: PAC recall is undefined, not 0,")
print("and the 'macro-F1' printed there averages in a class that does not exist in the split.")


# =====================================================================================
# ResNet-1D + RR pipeline (report appendix, ml/resnet/*.png). Different, later pipeline:
# labels N / V / 'a', where 'a' now holds A + a; record-wise split 33 / 7 / 8 records.
# =====================================================================================
RESNET = {
    "train": [[49353, 65, 274], [145, 4466, 21], [125, 4, 764]],
    "val":   [[13847, 32, 1044], [88, 662, 0], [76, 2, 41]],
    "test":  [[10004, 8, 406], [48, 1696, 3], [1464, 138, 82]],
}
PRINTED_SPLIT = {"train": 55217, "val": 15792, "test": 13849}
VAL_RECORDS = ["100", "101", "113", "116", "123", "215", "223"]
TEST_RECORDS = ["201", "202", "205", "207", "217", "228", "232", "233"]

# Per-record atrial premature beat counts (A, a) from PhysioNet's MIT-BIH directory of
# records. Transcribed from memory of that table -- verify with analysis/mitbih_label_audit.py.
PER_RECORD_A_a = {
    "100": (33, 0), "101": (3, 0), "113": (0, 6), "116": (1, 0), "123": (0, 0),
    "215": (3, 0), "223": (72, 1),
    "201": (30, 97), "202": (36, 19), "205": (3, 0), "207": (107, 0), "217": (0, 0),
    "228": (3, 0), "232": (1382, 0), "233": (7, 0),
}

print("\n" + "=" * 70 + "\nResNet-1D + RR pipeline\n" + "=" * 70)
pac_tot = 0
for k, cm in RESNET.items():
    sup = support(cm)
    pac_tot += sup[2]
    m = metrics(cm)
    print(f"  {k:<5} n={sum(sup):>6} (printed {PRINTED_SPLIT[k]})  support N/V/PAC={sup}  "
          + "  ".join(f"{c}: P={p:5.1%} R={r:5.1%}" for c, (p, r) in zip(CLASSES, m)))
print(f"  Total PAC = {pac_tot} = 2,546 'A' + 150 'a' = {2546 + 150}  -> PAC now means A + a")

for name, recs, key in (("val", VAL_RECORDS, "val"), ("test", TEST_RECORDS, "test")):
    s = sum(sum(PER_RECORD_A_a[r]) for r in recs)
    print(f"  {name} PAC from per-record table = {s}  vs confusion-matrix support {support(RESNET[key])[2]}")
share = PER_RECORD_A_a["232"][0] / support(RESNET["test"])[2]
print(f"  Record 232 alone = {PER_RECORD_A_a['232'][0]} of the test PACs ({share:.0%}).")
print("  Test PAC recall 4.9 % is therefore mostly one patient (record 232: sinus bradycardia with right bundle branch block).")
missed = RESNET["test"][2][0]
print(f"  PACs called Normal on test: {missed} of {support(RESNET['test'])[2]}")

# On-body inference (ml/resnet/inference_subject_*.png, hardware/scope/recordings_*.png)
for subj, n, fs in (("T", 3804, 190), ("Z", 3805, 190), ("Z2", 3834, 192)):
    print(f"  Subject_{subj}: {n} samples = {n/fs:.1f} s at {fs} Hz, but labelled as 360 Hz "
          f"({n/360:.1f} s); 180-sample window spans {180/fs*1e3:.0f} ms instead of 500 ms")
