"""Alias module name for Phase 18 vertical slice (member → QR).

Canonical implementation: ``test_vertical_slice_access.py``.
Re-exported so plan paths matching ``test_vertical_slice_member_qr`` resolve.
"""

from tests.e2e.test_vertical_slice_access import (  # noqa: F401
    test_vertical_slice_optional_notification_bridge,
    test_vertical_slice_org_member_qr_issue_validate,
    test_vertical_slice_staff_issue_validate_structured,
)
