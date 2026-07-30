"""台账完整性校验 — 8 条确定性规则。exit code 0 = PASS, 1 = blocker found."""
import csv
import sys
import re
from pathlib import Path

REGISTERS_DIR = Path(__file__).parent.parent.parent / "registers"

def load_csv(name: str) -> list[dict]:
    path = REGISTERS_DIR / name
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

def validate_id_format(record_id: str, prefix: str) -> bool:
    pattern = rf"^{prefix}-[A-Z]+-\d{{3}}$"
    return bool(re.match(pattern, record_id))

def check_v01(requirements: list[dict], traceability: list[dict]) -> list[str]:
    """每条 P0/P1 requirement 有 ≥1 条 traceability"""
    errors = []
    req_ids_with_trace = {t["requirement_id"] for t in traceability if t.get("requirement_id")}
    for req in requirements:
        if req.get("priority") in ("P0", "P1"):
            if req["requirement_id"] not in req_ids_with_trace:
                errors.append(f"V-01: {req['requirement_id']} (priority={req.get('priority')}) has no traceability")
    return errors

def check_v02(traceability: list[dict], evidence: list[dict]) -> list[str]:
    """traceability 中引用的 evidence_id 存在"""
    errors = []
    ev_ids = {e["evidence_id"] for e in evidence}
    for t in traceability:
        eid = t.get("evidence_id", "").strip()
        if eid and eid not in ev_ids:
            errors.append(f"V-02: traceability {t['trace_id']} references non-existent evidence {eid}")
    return errors

def check_v03(traceability: list[dict], requirements: list[dict]) -> list[str]:
    """traceability 中引用的 requirement_id 存在"""
    errors = []
    req_ids = {r["requirement_id"] for r in requirements}
    for t in traceability:
        rid = t.get("requirement_id", "").strip()
        if rid and rid not in req_ids:
            errors.append(f"V-03: traceability {t['trace_id']} references non-existent requirement {rid}")
    return errors

def check_v04(assumptions: list[dict]) -> list[str]:
    """assumptions 中 confidence=高 但没有 validation_method"""
    errors = []
    for a in assumptions:
        if a.get("confidence") == "高" and not a.get("validation_method", "").strip():
            errors.append(f"V-04: assumption {a.get('assumption_id', '?')} confidence=高 but no validation_method")
    return errors

def check_v05(risks: list[dict]) -> list[str]:
    """risks 中 impact=高 但没有 mitigation"""
    errors = []
    for r in risks:
        if r.get("impact") == "高" and not r.get("mitigation", "").strip():
            errors.append(f"V-05: risk {r.get('risk_id', '?')} impact=高 but no mitigation")
    return errors

def check_v06(evidence: list[dict]) -> list[str]:
    """evidence 的 source_grade 不为空"""
    errors = []
    for e in evidence:
        if not e.get("source_grade", "").strip():
            errors.append(f"V-06: evidence {e['evidence_id']} missing source_grade")
        if e.get("source_grade") not in ("A", "B", "C", "D", ""):
            errors.append(f"V-06: evidence {e['evidence_id']} invalid source_grade: {e.get('source_grade')}")
    return errors

def check_v07(evidence: list[dict], assumptions: list[dict], risks: list[dict],
              decisions: list[dict], requirements: list[dict], traceability: list[dict]) -> list[str]:
    """ID 格式符合规范，无跨文件重复"""
    errors = []
    seen = set()
    checks = [
        ("evidence", r"^EV-[A-Z]+-\d{3}$", evidence, "evidence_id"),
        ("assumption", r"^A-[A-Z]+-\d{3}$", assumptions, "assumption_id"),
        ("risk", r"^RISK-[A-Z]+-\d{3}$", risks, "risk_id"),
        ("decision", r"^DEC-[A-Z]+-\d{3}$", decisions, "decision_id"),
        ("requirement", r"^REQ-[A-Z]+-\d{3}$", requirements, "requirement_id"),
        ("traceability", r"^T-[A-Z]+-\d{3}$", traceability, "trace_id"),
    ]
    for label, pattern, records, key in checks:
        for rec in records:
            rid = rec.get(key, "").strip()
            if not rid:
                continue
            if not re.match(pattern, rid):
                errors.append(f"V-07: {label} {rid} does not match pattern {pattern}")
            if rid in seen:
                errors.append(f"V-07: duplicate ID {rid}")
            seen.add(rid)
    return errors

def check_v08(decisions: list[dict], requirements: list[dict]) -> list[str]:
    """已批准 artifact 有关联 decision_id — 信息性检查"""
    errors = []
    if decisions and not requirements:
        errors.append("V-08: INFO — decisions exist but no requirements yet (pre-PRD stage, expected)")
    return errors

def main():
    evidence = load_csv("evidence.csv")
    assumptions = load_csv("assumptions.csv")
    risks = load_csv("risks.csv")
    decisions = load_csv("decisions.csv")
    requirements = load_csv("requirements.csv")
    traceability = load_csv("traceability.csv")

    all_errors = []
    all_errors.extend(check_v01(requirements, traceability))
    all_errors.extend(check_v02(traceability, evidence))
    all_errors.extend(check_v03(traceability, requirements))
    all_errors.extend(check_v04(assumptions))
    all_errors.extend(check_v05(risks))
    all_errors.extend(check_v06(evidence))
    all_errors.extend(check_v07(evidence, assumptions, risks, decisions, requirements, traceability))
    all_errors.extend(check_v08(decisions, requirements))

    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} issues found:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED — all 8 checks passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
