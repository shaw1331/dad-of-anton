from __future__ import annotations

import enum


class TriggerType(str, enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    TESTING = "testing"
