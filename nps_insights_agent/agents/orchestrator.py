from agents import Agent

from nps_insights_agent.config import MODEL
from nps_insights_agent.agents.score_analyst import score_analyst_agent
from nps_insights_agent.agents.voice_of_customer import voice_of_customer_agent
from nps_insights_agent.agents.churn_risk import churn_risk_agent
from nps_insights_agent.agents.action_planner import action_planner_agent
from nps_insights_agent.agents.report_writer import report_writer_agent

ORCHESTRATOR_INSTRUCTIONS = """
You are the NPS Analytics Director orchestrating a full customer satisfaction investigation.
You coordinate five specialist agents and return the CEO brief as your final output.

PHASE 1 — DATA GATHERING (call all three simultaneously in a single step):
Call score_analysis, voice_analysis, and churn_analysis all at once with the input task.
Do not wait for one to finish before calling the next.
They are independent and must be issued as three parallel tool calls in a single response.
  - score_analysis:  NPS scorecard with trend and segment breakdown.
  - voice_analysis:  Customer comment themes, representative quotes, key insight.
  - churn_risk:      Revenue at risk by segment, data quality flags.

PHASE 2 — ACTION PLANNING (requires Phase 1 outputs):
Call action_planning with a message that includes ALL three Phase 1 outputs verbatim.
Format the input to action_planning as:
  [SCORE ANALYSIS]
  {full score_analysis output}
  [VOICE ANALYSIS]
  {full voice_analysis output}
  [CHURN RISK]
  {full churn_risk output}

PHASE 3 — FINAL BRIEF (requires Phase 1 + Phase 2 outputs):
Call report_writing with a message that includes ALL four analyst outputs verbatim.
Format the input to report_writing as:
  [SCORE ANALYSIS]
  {full score_analysis output}
  [VOICE ANALYSIS]
  {full voice_analysis output}
  [CHURN RISK]
  {full churn_risk output}
  [ACTION PLAN]
  {full action_planning output}

PHASE 4 — RETURN FINAL BRIEF:
Your final response is exactly the output from report_writing. Do not add commentary.

IMPORTANT:
- Phase 1 is non-negotiable: issue all three calls in one response (parallel).
- If any specialist agent returns an error, include the error verbatim in its section.
- Be patient — the workflow makes many API calls and may take 60-90 seconds.
"""


def make_orchestrator() -> Agent:
    """Create a fresh orchestrator per run to avoid state bleed between invocations."""
    return Agent(
        name="OrchestratorAgent",
        model=MODEL,
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        tools=[
            score_analyst_agent.as_tool(
                "score_analysis",
                "Run the NPS score analyst: computes overall NPS, monthly trend, and segment "
                "breakdowns by product, tenure, and channel. Returns a structured scorecard.",
            ),
            voice_of_customer_agent.as_tool(
                "voice_analysis",
                "Run the voice-of-customer analyst: identifies top complaint themes in 600 "
                "customer comments, counts frequency, calculates avg score per theme, and "
                "returns representative verbatim quotes.",
            ),
            churn_risk_agent.as_tool(
                "churn_risk",
                "Run the churn risk analyst: quantifies annual revenue at risk from expected "
                "detractor churn, segments by product and channel, and flags score-comment "
                "data quality mismatches.",
            ),
            action_planner_agent.as_tool(
                "action_planning",
                "Run the action planner: estimates NPS uplift and revenue saved for each top "
                "complaint theme, ranks fixes by both NPS and revenue impact, and returns the "
                "top 15 high-value detractors for callback. Pass all Phase 1 findings in the input.",
            ),
            report_writer_agent.as_tool(
                "report_writing",
                "Run the report writer: synthesizes all four specialist analyses into a one-page "
                "CEO brief with GREEN/AMBER/RED alert level. No tools — pure synthesis. "
                "Pass all Phase 1 and Phase 2 findings in the input.",
            ),
        ],
    )
