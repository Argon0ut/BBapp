from enum import Enum

class HairstylePreviewStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    APPROVED = "approved"
    CANCELLED = "cancelled"
