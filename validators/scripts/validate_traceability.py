"""追踪覆盖率校验。exit code 0 = 覆盖率 ≥80%, 1 = 覆盖率不足."""
import csv
import sys
from pathlib import Path

REGISTERS_DIR = Path(__file__).parent.parent.parent / "registers"

def main():
    with open(REGISTERS_DIR / "requirements.csv") as f:
        requirements = list(csv.DictReader(f))
    with open(REGISTERS_DIR / "traceability.csv") as f:
        traceability = list(csv.DictReader(f))

    p0_p1_reqs = [r for r in requirements if r.get("priority") in ("P0", "P1")]
    if not p0_p1_reqs:
        print("No P0/P1 requirements found — nothing to trace")
        sys.exit(0)

    traced_ids = {t["requirement_id"] for t in traceability if t.get("requirement_id")}
    total = len(p0_p1_reqs)
    covered = sum(1 for r in p0_p1_reqs if r["requirement_id"] in traced_ids)
    pct = (covered / total) * 100

    print(f"Traceability coverage: {covered}/{total} ({pct:.0f}%)")
    for r in p0_p1_reqs:
        if r["requirement_id"] not in traced_ids:
            print(f"  UNTRACED: {r['requirement_id']} — {r.get('title', '')}")

    if pct < 80:
        print(f"FAIL: coverage {pct:.0f}% < 80% threshold")
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
