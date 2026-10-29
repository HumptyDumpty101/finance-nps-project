import json
import math
from functools import lru_cache

import pandas as pd
from agents import function_tool

from nps_insights_agent.config import DATA_PATH, CHURN_RATES, MOE_THRESHOLD


def classify(score: int) -> str:
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    return "detractor"


def nps_from_counts(promoters: int, detractors: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((promoters / total - detractors / total) * 100, 1)


def margin_of_error(n: int) -> float | None:
    """95% CI margin of error for an NPS proportion."""
    if n < MOE_THRESHOLD and n > 0:
        return round(1.96 * math.sqrt(0.25 / n) * 100, 1)
    return None


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["category"] = df["score"].apply(classify)
    return df


@function_tool
def get_nps_overview() -> str:
    """Return overall NPS, promoter/passive/detractor breakdown, monthly NPS trend, and total respondents.
    All percentages are rounded to one decimal place. NPS = (promoters% - detractors%).
    """
    df = load_df()
    total = len(df)
    cats = df["category"].value_counts()
    promoters  = int(cats.get("promoter", 0))
    passives   = int(cats.get("passive", 0))
    detractors = int(cats.get("detractor", 0))

    monthly = {}
    for month, grp in df.groupby("month"):
        n = len(grp)
        p = int((grp["category"] == "promoter").sum())
        pa = int((grp["category"] == "passive").sum())
        d = int((grp["category"] == "detractor").sum())
        monthly[str(month)] = {
            "nps":        nps_from_counts(p, d, n),
            "n":          n,
            "promoters":  p,
            "passives":   pa,
            "detractors": d,
        }

    return json.dumps({
        "overall_nps":       nps_from_counts(promoters, detractors, total),
        "total_respondents": total,
        "promoters":  {"count": promoters,  "pct": round(promoters  / total * 100, 1)},
        "passives":   {"count": passives,   "pct": round(passives   / total * 100, 1)},
        "detractors": {"count": detractors, "pct": round(detractors / total * 100, 1)},
        "monthly_nps": monthly,
    })


@function_tool
def get_nps_by_segment(segment: str) -> str:
    """Return NPS broken down by a demographic or channel segment.
    Each group includes NPS, sample size, category counts, and a margin-of-error flag for n < 30.

    Args:
        segment: Column to segment by — must be one of: "product", "tenure", or "channel".
    """
    df = load_df()
    if segment not in ("product", "tenure", "channel"):
        return json.dumps({"error": f"Invalid segment '{segment}'. Choose: product, tenure, channel."})

    result = {}
    for val, grp in df.groupby(segment):
        n  = len(grp)
        p  = int((grp["category"] == "promoter").sum())
        pa = int((grp["category"] == "passive").sum())
        d  = int((grp["category"] == "detractor").sum())
        moe = margin_of_error(n)
        result[str(val)] = {
            "nps":                    nps_from_counts(p, d, n),
            "n":                      n,
            "promoters":              p,
            "passives":               pa,
            "detractors":             d,
            "low_sample_warning":     moe is not None,
            "margin_of_error_95pct":  moe,
        }

    return json.dumps({segment: result})
