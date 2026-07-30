"""Gate 条件校验 — 检查指定 Gate 的所有 artifact 是否已通过 review."""
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: validate_gate.py <gate_request.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        gate = json.load(f)

    errors = []
    for art in gate.get("artifacts", []):
        if art["review_verdict"] == "rejected":
            errors.append(f"{art['artifact_id']}: rejected by reviewer — cannot proceed")
        if art["review_verdict"] == "conditional":
            errors.append(f"{art['artifact_id']}: conditional approval — verify conditions met")

    if not gate.get("validation_status", {}).get("registers_check"):
        errors.append("registers_check: FAILED — run validate_registers.py first")
    if not gate.get("validation_status", {}).get("traceability_check"):
        errors.append("traceability_check: FAILED — run validate_traceability.py first")

    if errors:
        print(f"GATE BLOCKED — {len(errors)} issues:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)
    else:
        print(f"GATE {gate['gate_id']}: READY for human approval")
        print(f"Decision options: {gate.get('decision_options', [])}")
        sys.exit(0)

if __name__ == "__main__":
    main()
