"""M1 — Smoke-test all tool functions without any LLM calls."""
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from nps_insights_agent.tools.survey_tools import get_nps_overview, get_nps_by_segment
from nps_insights_agent.tools.theme_tools import get_comment_themes
from nps_insights_agent.tools.whatif_tools import (
    get_revenue_at_risk,
    find_score_comment_mismatches,
    estimate_fix_impact,
    get_callback_list,
)


def _print(label: str, raw: str) -> None:
    data = json.loads(raw)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))


def call(tool, *args, **kwargs):
    """Call the underlying function from a @function_tool decorated tool."""
    return tool.__wrapped__(*args, **kwargs)


def main() -> None:
    _print("get_nps_overview()", call(get_nps_overview))
    _print("get_nps_by_segment('product')", call(get_nps_by_segment, "product"))
    _print("get_nps_by_segment('tenure')", call(get_nps_by_segment, "tenure"))
    _print("get_nps_by_segment('channel')", call(get_nps_by_segment, "channel"))
    _print("get_comment_themes()", call(get_comment_themes))
    _print("get_revenue_at_risk()", call(get_revenue_at_risk))
    _print("find_score_comment_mismatches()", call(find_score_comment_mismatches))
    _print("estimate_fix_impact('app_crashes')", call(estimate_fix_impact, "app_crashes"))
    _print("estimate_fix_impact('hidden_charges')", call(estimate_fix_impact, "hidden_charges"))
    _print("get_callback_list(5)", call(get_callback_list, 5))

    print("\nAll tools ran without errors.\n")


if __name__ == "__main__":
    main()
