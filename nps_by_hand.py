"""M0 — Baseline NPS calculation without any agent or LLM."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "nps_survey.csv"


def classify(score: int) -> str:
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    return "detractor"


def nps(df: pd.DataFrame) -> float:
    total = len(df)
    p = (df["category"] == "promoter").sum()
    d = (df["category"] == "detractor").sum()
    return round((p / total - d / total) * 100, 1)


def main() -> None:
    df = pd.read_csv(DATA)
    df["category"] = df["score"].apply(classify)

    overall = nps(df)
    print(f"Overall NPS (Jul–Sep 2026): {overall}")
    print()

    print("Monthly NPS:")
    for month, grp in df.groupby("month"):
        monthly_nps = nps(grp)
        n = len(grp)
        p = (grp["category"] == "promoter").sum()
        pa = (grp["category"] == "passive").sum()
        d = (grp["category"] == "detractor").sum()
        print(
            f"  {month}: NPS = {monthly_nps:+.1f}  "
            f"(n={n}, promoters={p}, passives={pa}, detractors={d})"
        )

    print()
    total = len(df)
    p_total = (df["category"] == "promoter").sum()
    pa_total = (df["category"] == "passive").sum()
    d_total = (df["category"] == "detractor").sum()
    print(f"Totals: promoters={p_total} ({p_total/total*100:.1f}%)  "
          f"passives={pa_total} ({pa_total/total*100:.1f}%)  "
          f"detractors={d_total} ({d_total/total*100:.1f}%)")


if __name__ == "__main__":
    main()
