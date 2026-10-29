import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DATA_PATH = Path(__file__).parent.parent / "data" / "nps_survey.csv"

CHURN_RATES = {
    "promoter": 0.03,
    "passive":  0.10,
    "detractor": 0.25,
}

MOE_THRESHOLD = 30  # segments below this get a margin-of-error flag

THEMES = {
    "app_crashes":         ["crash", "crashes", "crashing", "freeze", "froze", "hang", "not loading", "broken", "glitch"],
    "app_slow":            ["slow", "sluggish", "lag", "peak hours", "takes time", "buffering"],
    "long_wait_times":     ["wait", "waiting", "queue", "long time", "delay", "hold", "hours", "days", "takes forever"],
    "hidden_charges":      ["charge", "charged", "fee", "fees", "hidden", "deducted", "deduct", "penalty", "annual fee", "extra charge", "unexpected"],
    "loan_emi":            ["loan", "emi", "interest", "mortgage", "home loan", "personal loan", "processing fee", "disburs"],
    "customer_support":    ["support", "customer care", "helpline", "call centre", "resolve", "complaint", "unresponsive", "call center"],
    "branch_experience":   ["branch", "staff", "counter", "in-person", "walk-in", "manager", "teller"],
    "digital_onboarding":  ["kyc", "account opening", "onboard", "activation", "verification", "document", "submit"],
    "rewards_cashback":    ["cashback", "reward", "rewards", "points", "offers", "benefits", "discount", "milestone", "spend target"],
    "statements_access":   ["statement", "passbook", "transaction history", "balance check", "view transaction"],
}

POSITIVE_WORDS = {
    "amazing", "excellent", "great", "good", "wonderful", "smooth", "easy",
    "quick", "fast", "helpful", "friendly", "love", "best", "perfect", "happy",
    "satisfied", "appreciate", "thank", "impressed", "outstanding", "superb",
    "brilliant", "fantastic", "awesome", "seamless", "reliable",
}

NEGATIVE_WORDS = {
    "crash", "freeze", "slow", "wait", "bad", "worst", "terrible", "rude",
    "problem", "issue", "error", "difficult", "horrible", "frustrat", "angry",
    "disappoint", "charged", "wrong", "incorrect", "missing", "delay", "poor",
    "useless", "awful", "fails", "fail", "not working", "broken", "glitch",
    "long", "queue", "penalty", "hidden", "complaint",
}
