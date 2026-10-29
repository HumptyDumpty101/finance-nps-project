"""M4 — Independent fact-checker: re-computes headline numbers and asserts correctness.
Run standalone: python fact_check.py
Returns exit code 0 on PASS, 1 on FAIL.
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import pandas as pd

from nps_insights_agent.config import DATA_PATH, CHURN_RATES
from nps_insights_agent.tools.survey_tools import get_nps_overview, get_nps_by_segment
from nps_insights_agent.tools.whatif_tools import get_revenue_at_risk

PASS = "✓ PASS"
FAIL = "✗ FAIL"


def _classify(score: int) -> str:
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    return "detractor"


def recompute_nps(df: pd.DataFrame) -> dict:
    """Independently recompute NPS from raw CSV — does not call any tool."""
    total = len(df)
    p = int((df["score"] >= 9).sum())
    d = int((df["score"] <= 6).sum())
    overall = round((p / total - d / total) * 100, 1)

    monthly = {}
    for month, grp in df.groupby("month"):
        n = len(grp)
        pm = int((grp["score"] >= 9).sum())
        dm = int((grp["score"] <= 6).sum())
        monthly[str(month)] = round((pm / n - dm / n) * 100, 1)

    return {"overall": overall, "total": total, "promoters": p, "detractors": d, "monthly": monthly}


def recompute_revenue_at_risk(df: pd.DataFrame) -> float:
    """Independently recompute total revenue at risk — does not call any tool."""
    df = df.copy()
    df["category"] = df["score"].apply(_classify)
    df["rar"] = df.apply(
        lambda r: r["annual_revenue_inr"] * CHURN_RATES[r["category"]], axis=1
    )
    return round(df["rar"].sum())


def check(label: str, expected, actual, tolerance: float = 0.0) -> bool:
    if isinstance(expected, float) and tolerance > 0:
        ok = abs(expected - actual) <= tolerance
    else:
        ok = expected == actual
    status = PASS if ok else FAIL
    print(f"  {status}  {label}: expected={expected}, got={actual}")
    return ok


def main() -> None:
    print("\nFACT-CHECK REPORT")
    print("=" * 50)
    df = pd.read_csv(DATA_PATH)
    truth = recompute_nps(df)
    rar_truth = recompute_revenue_at_risk(df)

    # --- verify tool: get_nps_overview ---
    print("\n[1] get_nps_overview()")
    overview = json.loads(get_nps_overview.__wrapped__())
    results = [
        check("overall_nps",        truth["overall"],    overview["overall_nps"]),
        check("total_respondents",  truth["total"],      overview["total_respondents"]),
        check("promoter_count",     truth["promoters"],  overview["promoters"]["count"]),
        check("detractor_count",    truth["detractors"], overview["detractors"]["count"]),
    ]
    for month, expected_nps in truth["monthly"].items():
        results.append(
            check(f"monthly_nps[{month}]", expected_nps, overview["monthly_nps"][month]["nps"])
        )

    # --- verify tool: get_revenue_at_risk ---
    print("\n[2] get_revenue_at_risk()")
    rar = json.loads(get_revenue_at_risk.__wrapped__())
    results.append(
        check("total_revenue_at_risk_inr", rar_truth, rar["total_revenue_at_risk_inr"], tolerance=1)
    )

    # --- verify tool: get_nps_by_segment ---
    print("\n[3] get_nps_by_segment — spot-check product totals sum to 600")
    product_seg = json.loads(get_nps_by_segment.__wrapped__("product"))["product"]
    n_sum = sum(v["n"] for v in product_seg.values())
    results.append(check("product_segment_n_sum", truth["total"], n_sum))

    # --- summary ---
    passed = sum(results)
    total_checks = len(results)
    print(f"\n{'='*50}")
    print(f"RESULT: {passed}/{total_checks} checks passed")
    if passed == total_checks:
        print("FACT-CHECK: PASS — all headline numbers verified.\n")
        sys.exit(0)
    else:
        print("FACT-CHECK: FAIL — discrepancies found. Do not deliver brief.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
