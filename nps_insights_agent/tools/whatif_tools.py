import json
from agents import function_tool

from nps_insights_agent.config import CHURN_RATES, THEMES, POSITIVE_WORDS, NEGATIVE_WORDS
from nps_insights_agent.tools.survey_tools import load_df, nps_from_counts
from nps_insights_agent.tools.theme_tools import assign_themes


def _revenue_at_risk(row) -> float:
    return row["annual_revenue_inr"] * CHURN_RATES[row["category"]]


@function_tool
def get_revenue_at_risk() -> str:
    """Quantify total annual revenue at risk from expected churn.
    Churn assumptions: promoter 3%, passive 10%, detractor 25%.
    Returns total, breakdown by product, breakdown by channel, and top-10 individual accounts.
    """
    df = load_df()
    df = df.copy()
    df["revenue_at_risk"] = df.apply(_revenue_at_risk, axis=1)

    total_rar = df["revenue_at_risk"].sum()

    def segment_summary(col: str) -> dict:
        out = {}
        for val, grp in df.groupby(col):
            det = grp[grp["category"] == "detractor"]
            out[str(val)] = {
                "total_revenue_at_risk_inr": round(grp["revenue_at_risk"].sum()),
                "n_detractors": len(det),
                "detractor_revenue_at_risk_inr": round(det["revenue_at_risk"].sum()),
                "avg_annual_revenue_inr": round(grp["annual_revenue_inr"].mean()),
            }
        return out

    return json.dumps({
        "total_revenue_at_risk_inr": round(total_rar),
        "by_product": segment_summary("product"),
        "by_channel": segment_summary("channel"),
    })


@function_tool
def find_score_comment_mismatches() -> str:
    """Identify responses where the numeric score and comment sentiment contradict each other.
    Flags detractors (0-6) with clearly positive comments and promoters (9-10) with clearly
    negative comments. Returns count, percentage of total, and up to 20 examples.
    """
    df = load_df()
    mismatches = []

    for _, row in df.iterrows():
        comment = str(row["comment"]) if row["comment"] and str(row["comment"]).strip() else ""
        if not comment:
            continue
        text = comment.lower()
        pos_hits = sum(1 for w in POSITIVE_WORDS if w in text)
        neg_hits = sum(1 for w in NEGATIVE_WORDS if w in text)

        mismatch_type = None
        if row["category"] == "detractor" and pos_hits >= 2 and neg_hits == 0:
            mismatch_type = "detractor_positive_comment"
        elif row["category"] == "promoter" and neg_hits >= 2 and pos_hits == 0:
            mismatch_type = "promoter_negative_comment"

        if mismatch_type:
            mismatches.append({
                "response_id":   str(row["response_id"]),
                "score":         int(row["score"]),
                "category":      row["category"],
                "comment":       comment[:120],
                "mismatch_type": mismatch_type,
            })

    total = len(df)
    return json.dumps({
        "total_mismatches":     len(mismatches),
        "pct_of_responses":    round(len(mismatches) / total * 100, 1) if total else 0,
        "examples":            mismatches[:20],
    })


@function_tool
def estimate_fix_impact(theme: str) -> str:
    """Estimate the NPS improvement and revenue saved if all detractors mentioning a theme
    were moved to passive (neutral) status. Uses deterministic Python — no LLM reasoning.

    Args:
        theme: Theme key to analyze — one of: app_crashes, app_slow, long_wait_times,
               hidden_charges, loan_emi, customer_support, branch_experience,
               digital_onboarding, rewards_cashback, statements_access.
    """
    if theme not in THEMES:
        return json.dumps({
            "error": f"Unknown theme '{theme}'. Valid themes: {', '.join(THEMES)}"
        })

    df = load_df()
    total = len(df)

    df = df.copy()
    df["themes"] = df["comment"].apply(assign_themes)
    theme_df = df[df["themes"].apply(lambda ts: theme in ts)]
    detractors_in_theme = theme_df[theme_df["category"] == "detractor"]
    n_affected = len(detractors_in_theme)

    # NPS delta: each moved detractor stops being −1 and becomes 0
    # Delta = n_affected / total * 100 (each detractor contributes −1/total to NPS)
    nps_delta = round(n_affected / total * 100, 2) if total else 0

    # Revenue saved = (detractor_churn - passive_churn) × affected revenue
    churn_delta = CHURN_RATES["detractor"] - CHURN_RATES["passive"]  # 0.15
    revenue_saved = round(
        detractors_in_theme["annual_revenue_inr"].sum() * churn_delta
    )

    return json.dumps({
        "theme":                theme,
        "affected_detractors":  n_affected,
        "nps_points_gained":    nps_delta,
        "annual_revenue_saved_inr": revenue_saved,
        "churn_delta_assumed":  churn_delta,
        "note": "Assumes detractors move to passive only (conservative estimate).",
    })


@function_tool
def get_callback_list(top_n: int) -> str:
    """Return the top N detractors sorted by annual revenue (highest first) as a priority callback list.
    Each entry includes response_id, product, channel, score, comment snippet, annual revenue, and revenue at risk.

    Args:
        top_n: Number of detractors to return (e.g. 10 or 15).
    """
    df = load_df()
    detractors = df[df["category"] == "detractor"].copy()
    detractors["revenue_at_risk"] = detractors["annual_revenue_inr"] * CHURN_RATES["detractor"]
    top = detractors.nlargest(int(top_n), "annual_revenue_inr")

    records = []
    for _, row in top.iterrows():
        records.append({
            "response_id":          str(row["response_id"]),
            "product":              str(row["product"]),
            "channel":              str(row["channel"]),
            "score":                int(row["score"]),
            "comment":              str(row["comment"])[:100] if row["comment"] else "",
            "annual_revenue_inr":   int(row["annual_revenue_inr"]),
            "revenue_at_risk_inr":  round(row["revenue_at_risk"]),
        })

    return json.dumps({
        "top_n":            len(records),
        "callback_list":    records,
        "total_detractors": len(detractors),
    })
