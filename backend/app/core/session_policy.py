"""Idle and step-up windows for authenticated sessions."""

from datetime import timedelta

STEP_UP_MAX_AGE = timedelta(minutes=5)
PRIVILEGED_IDLE = timedelta(minutes=30)
STEP_UP_REQUIRED = "step_up_required"

PRIVILEGED_ROLE_NAMES = frozenset(
    {
        "PLATFORM_SUPER_ADMIN",
        "FEDERATION_ADMIN",
        "FEDERATION_ANALYST",
        "FEDERATION_SUPPORT",
        "GYM_OWNER",
        "GYM_ADMIN",
        "GYM_MANAGER",
        "ACCOUNTANT",
        "FRONT_DESK",
        "TRAINER",
    }
)
