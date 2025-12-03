from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    """
    One row in the incident timeline.
    This is generic enough to work for tickets, logs, chats, etc.
    """

    id: int
    timestamp: datetime
    source: str
    message: str

    author: Optional[str] = None
    event_type: Optional[str] = None

    phase: Literal[
        "unknown",
        "detection",
        "investigation",
        "mitigation",
        "resolution",
    ] = "unknown"
    