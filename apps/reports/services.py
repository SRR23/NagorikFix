"""
Small domain helpers for report lifecycle.

Keep workflow rules here so views stay thin. Escalation / SLA / AI
duplicate detection can plug in later without rewriting views.
"""
from django.utils import timezone

from utils.constants import STATUS_RESOLVED


def apply_report_updates(report, *, status=None, priority=None, assigned_to=..., clear_assignee=False):
    """
    Apply allowed admin/officer updates and stamp resolved_at when needed.

    assigned_to uses Ellipsis as "not provided". Pass clear_assignee=True
    (or assigned_to=None explicitly via the field) to unassign.
    """
    if status is not None:
        report.status = status
        if status == STATUS_RESOLVED:
            if report.resolved_at is None:
                report.resolved_at = timezone.now()
        else:
            report.resolved_at = None

    if priority is not None:
        report.priority = priority

    if clear_assignee:
        report.assigned_to = None
    elif assigned_to is not ...:
        report.assigned_to = assigned_to

    report.save()
    return report
