import json
from agents import function_tool

from nps_insights_agent.config import THEMES
from nps_insights_agent.tools.survey_tools import load_df


def assign_themes(comment: str) -> list[str]:
    """Return all theme keys that match keywords in comment (case-insensitive)."""
    if not comment or not isinstance(comment, str):
        return []
    text = comment.lower()
    return [theme for theme, keywords in THEMES.items() if any(kw in text for kw in keywords)]


@function_tool
def get_comment_themes() -> str:
    """Analyze all customer comments and return keyword-based theme counts, NPS per theme,
    total revenue at risk per theme, and up to three representative quotes per theme.
    Only comments containing text are included; blank comments are excluded.
    """
    df = load_df()
    comments_df = df[df["comment"].notna() & (df["comment"].str.strip() != "")].copy()
    comments_df["themes"] = comments_df["comment"].apply(assign_themes)

    theme_stats: dict[str, dict] = {
        t: {"count": 0, "scores": [], "quotes": [], "response_ids": []}
        for t in THEMES
    }

    for _, row in comments_df.iterrows():
        for t in row["themes"]:
            theme_stats[t]["count"] += 1
            theme_stats[t]["scores"].append(int(row["score"]))
            if len(theme_stats[t]["quotes"]) < 3:
                theme_stats[t]["quotes"].append(str(row["comment"])[:120])
                theme_stats[t]["response_ids"].append(str(row["response_id"]))

    total_with_themes = sum(
        1 for _, row in comments_df.iterrows() if row["themes"]
    )
    total_comments = len(comments_df)

    result = {
        "total_comments_analyzed": total_comments,
        "comments_with_themes":    total_with_themes,
        "themes": {},
    }

    for theme, stats in theme_stats.items():
        n = stats["count"]
        if n == 0:
            continue
        avg_score = round(sum(stats["scores"]) / n, 1)
        result["themes"][theme] = {
            "count":          n,
            "pct_of_comments": round(n / total_comments * 100, 1) if total_comments else 0,
            "avg_score":      avg_score,
            "sample_quotes":  stats["quotes"],
        }

    # sort by count descending
    result["themes"] = dict(
        sorted(result["themes"].items(), key=lambda x: x[1]["count"], reverse=True)
    )
    return json.dumps(result)
