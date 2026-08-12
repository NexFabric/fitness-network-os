"""Public marketing telemetry — honest, non-PII design targets only.

No fabricated live production metrics. Real timeseries require a dedicated
metrics pipeline (Phase 27 P2+).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/public")
async def get_public_telemetry():
    """Design-target SLAs for marketing — not live measured production stats."""
    return {
        "kind": "design_targets",
        "disclaimer": "These are product design targets, not live production measurements.",
        "targets": {
            "uptime_target": "99.9%",
            "data_loss_target": "zero_planned",
            "access_scale_target": "high_volume_per_day",
        },
    }
