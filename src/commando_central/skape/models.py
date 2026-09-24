from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar
from uuid import uuid4

VALID_STATUSES: ClassVar[set[str]] = {"draft", "active", "completed", "archived"}
VALID_TASK_STATUSES: ClassVar[set[str]] = {"todo", "in_progress", "completed", "blocked"}


def _normalize_status(status: str, allowed: set[str], *, label: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized not in allowed:
        raise ValueError(f"Invalid {label} status '{status}'. Supported statuses: {sorted(allowed)}")
    return normalized


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
        self.status = _normalize_status(self.status, VALID_STATUSES, label="idea")


@dataclass(slots=True)
class Project:
    title: str
    description: str = ""
    status: str = "draft"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        title = (self.title or "").strip()
        if not title:
            raise ValueError("Project title cannot be empty.")

        self.title = title
        self.description = (self.description or "").strip()
        self.status = _normalize_status(self.status, VALID_STATUSES, label="project")


@dataclass(slots=True)
class Task:
    project_id: str
    title: str
    description: str = ""
    status: str = "todo"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        project_id = (self.project_id or "").strip()
        if not project_id:
            raise ValueError("Task project_id cannot be empty.")

        title = (self.title or "").strip()
        if not title:
            raise ValueError("Task title cannot be empty.")

        self.project_id = project_id
        self.title = title
        self.description = (self.description or "").strip()
        self.status = _normalize_status(self.status, VALID_TASK_STATUSES, label="task")
