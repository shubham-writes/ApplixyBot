PLAN_LIMITS = {
    "free": {
        "jobs_per_day": 5,
        "cover_letters_per_day": 1,
        "saved_jobs_max": 5,
        "application_tracking_max": 10,
        "job_match_score": False,
        "follow_up_reminders": False,
        "weekly_digest": False,
        "llm_model": "fast",        # Llama 3 8B
    },
    "pro": {
        "jobs_per_day": 999,        # effectively unlimited
        "cover_letters_per_day": 10,
        "saved_jobs_max": 200,
        "application_tracking_max": 999,
        "job_match_score": True,
        "follow_up_reminders": True,
        "weekly_digest": True,
        "llm_model": "quality",     # Llama 3 70B
    },
}

PLAN_PRICES = {
    "pro": {
        "inr": 99,
        "display": "₹99/month",
    }
}

def get_limit(plan: str, feature: str):
    # Default to 'free' plan if plan is invalid or None
    if not plan or plan not in PLAN_LIMITS:
        plan = "free"
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(feature)
