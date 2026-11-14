"""One-off helper: records infer() outputs from the ORIGINAL engine into tests/golden.json."""
import itertools, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bunk_meter as bm

atts = sorted({0, 10, 37.5, 50, 69.9, 70, 72, 74, 74.5, 75, 75.5, 78, 80, 81.5, 85, 90, 95, 100})
creds = [1, 1.5, 2, 2.5, 3, 3.5, 4]
temps = [0, 2, 4, 5, 6, 8, 10]
out = []
for a, c, t in itertools.product(atts, creds, temps):
    fz, fired, os_, xs, agg, score = bm.infer({"attendance": a, "credits": c, "temptation": t})
    out.append({"in": [a, c, t], "score": score, "out_strength": os_, "area": float(agg.sum()),
                "fired": [[s, *r] for s, *r in fired]})
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden.json")
json.dump(out, open(path, "w"), indent=0)
print(len(out), "cases")
