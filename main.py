"""Entry point — runs the full NPS analysis pipeline.

Usage:
  python main.py           # run analysis, print brief
  python main.py --trace   # same with verbose tool-call tracing
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from agents import Runner, enable_verbose_stdout_logging
from nps_insights_agent.agents.orchestrator import make_orchestrator


PROMPT = (
    "Analyze Q3 2026 NPS survey data (600 responses, Jul–Sep 2026). "
    "Answer the CEO's four questions: "
    "(1) How severe is the NPS score drop? "
    "(2) What are the root causes? "
    "(3) How much revenue is at risk? "
    "(4) What fixes should we prioritize and in what order? "
    "Follow the full workflow: run Phase 1 analysts in parallel, then action planning, "
    "then produce the one-page leadership brief."
)


def run(trace: bool = False) -> None:
    if trace:
        enable_verbose_stdout_logging()
        print("[TRACE MODE ENABLED — tool calls will be logged]\n")

    print("Starting NPS analysis pipeline...")
    print("Phase 1 will run three analysts in parallel. This may take 60-90 seconds.\n")

    orchestrator = make_orchestrator()
    result = Runner.run_sync(orchestrator, PROMPT, max_turns=30)

    print("\n" + "=" * 70)
    print("NPS ANALYST BRIEF")
    print("=" * 70)
    print(result.final_output)

    # M4: run fact-check independently after the brief is produced
    print("\n" + "=" * 70)
    print("RUNNING FACT-CHECK...")
    print("=" * 70)
    import subprocess
    fc = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "fact_check.py")],
        capture_output=False,
    )
    if fc.returncode != 0:
        print("\n[WARNING] Fact-check failed — review numbers before sharing the brief.")
    else:
        print("\n[OK] Fact-check passed — numbers verified against source data.")


if __name__ == "__main__":
    trace = "--trace" in sys.argv
    run(trace=trace)
