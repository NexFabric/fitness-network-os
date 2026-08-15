from fastapi import APIRouter

from app.api.v1.endpoints import (
    access,
    admin,
    auth,
    break_glass,
    classes,
    dashboard,
    data_import,
    devices,
    entitlements,
    finance,
    locations,
    me,
    members,
    memberships,
    mfa,
    notifications,
    onboarding,
    plans,
    reception,
    reports,
    staff,
    telemetry,
    trainers,
)

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(
    break_glass.router, prefix="/admin/break-glass", tags=["break-glass"]
)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(mfa.router, prefix="/auth/mfa", tags=["mfa"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reception.router, prefix="/reception", tags=["reception"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
# Creation sits with the catalogue it depends on, but keeps the /memberships path.
api_router.include_router(
    plans.membership_router, prefix="/memberships", tags=["memberships"]
)
api_router.include_router(
    memberships.router, prefix="/memberships", tags=["memberships"]
)
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(entitlements.router, prefix="/members", tags=["entitlements"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(access.router, prefix="/access", tags=["access"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(trainers.router, prefix="/trainers", tags=["trainers"])
api_router.include_router(data_import.router, prefix="/import", tags=["import"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
