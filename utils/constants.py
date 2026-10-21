"""
Report status, priority, and media constants shared across apps.
"""

STATUS_PENDING = "pending"
STATUS_ASSIGNED = "assigned"
STATUS_IN_PROGRESS = "in_progress"
STATUS_RESOLVED = "resolved"
STATUS_REJECTED = "rejected"

REPORT_STATUS_CHOICES = [
    (STATUS_PENDING, "Pending"),
    (STATUS_ASSIGNED, "Assigned"),
    (STATUS_IN_PROGRESS, "In Progress"),
    (STATUS_RESOLVED, "Resolved"),
    (STATUS_REJECTED, "Rejected"),
]

PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"

PRIORITY_CHOICES = [
    (PRIORITY_HIGH, "High"),
    (PRIORITY_MEDIUM, "Medium"),
    (PRIORITY_LOW, "Low"),
]

MEDIA_IMAGE = "image"
MEDIA_VIDEO = "video"

MEDIA_TYPE_CHOICES = [
    (MEDIA_IMAGE, "Image"),
    (MEDIA_VIDEO, "Video"),
]

# Nagorik may attach at most this many photos when submitting a report.
MAX_REPORT_PHOTOS = 3

# Default seed categories.
DEFAULT_CATEGORIES = [
    {"name": "Road", "slug": "road", "sort_order": 1},
    {"name": "Drainage", "slug": "drainage", "sort_order": 2},
    {"name": "Electricity", "slug": "electricity", "sort_order": 3},
    {"name": "Bridge", "slug": "bridge", "sort_order": 4},
    {"name": "Street Light", "slug": "street-light", "sort_order": 5},
    {"name": "Water Supply", "slug": "water-supply", "sort_order": 6},
    {"name": "Other", "slug": "other", "sort_order": 99},
]
