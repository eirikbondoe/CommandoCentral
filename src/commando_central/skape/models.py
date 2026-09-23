from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar
from uuid import uuid4

VALID_STATUSES: ClassVar[set[str]] = {"draft", "active", "completed", "archived"}


@dataclass(slots=True)
class Idea:
    title: str
    description: str = ""
    status: str = "draft"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        title = (self.title or "").strip()
        if not title:
            raise ValueError("Idea title cannot be empty.")

        self.title = title
        self.description = (self.description or "").strip()
        self.status = self._normalize_status(self.status)

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = (status or "").strip().lower()
        if normalized not in VALID_STATUSES:
            raise ValueError(
                f"Invalid idea status '{status}'. Supported statuses: {sorted(VALID_STATUSES)}"
            )
        return normalized
