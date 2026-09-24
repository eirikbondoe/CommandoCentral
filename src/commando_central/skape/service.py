from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Protocol

from .models import Idea, VALID_STATUSES


class IdeaNotFoundError(KeyError):
    """Raised when an idea cannot be found in the service."""


class IdeaStore(Protocol):
    def save(self, idea: Idea) -> None: ...

    def get(self, idea_id: str) -> Idea | None: ...

    def list(self) -> list[Idea]: ...

    def update_status(self, idea_id: str, status: str) -> None: ...


class InMemoryIdeaStore:
    def __init__(self) -> None:
        self._ideas: dict[str, Idea] = {}

    def save(self, idea: Idea) -> None:
        self._ideas[idea.id] = idea

    def get(self, idea_id: str) -> Idea | None:
        return self._ideas.get(idea_id)

    def list(self) -> list[Idea]:
        return list(self._ideas.values())

    def update_status(self, idea_id: str, status: str) -> None:
        self._ideas[idea_id].status = status


class SQLiteIdeaStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ideas (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _row_to_idea(row: sqlite3.Row) -> Idea:
        created_at = datetime.fromisoformat(row["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return Idea(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=created_at,
        )

    def save(self, idea: Idea) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ideas (id, title, description, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    idea.id,
                    idea.title,
                    idea.description,
                    idea.status,
                    idea.created_at.isoformat(),
                ),
            )
            connection.commit()

    def get(self, idea_id: str) -> Idea | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT id, title, description, status, created_at FROM ideas WHERE id = ?",
                (idea_id,),
            ).fetchone()
        return None if row is None else self._row_to_idea(row)

    def list(self) -> list[Idea]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, title, description, status, created_at
                FROM ideas
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [self._row_to_idea(row) for row in rows]

    def update_status(self, idea_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE ideas SET status = ? WHERE id = ?", (status, idea_id))
            connection.commit()


class SkapeService:
    def __init__(self, *, db_path: str | None = None, store: IdeaStore | None = None) -> None:
        if db_path and store is not None:
            raise ValueError("Use either db_path or store, not both.")
        self._store = store or (SQLiteIdeaStore(db_path) if db_path else InMemoryIdeaStore())

    def create_idea(self, title: str, description: str = "") -> Idea:
        idea = Idea(title=title, description=description)
        self._store.save(idea)
        return idea

    def get_idea(self, idea_id: str) -> Idea:
        idea = self._store.get(idea_id)
        if idea is None:
            raise IdeaNotFoundError(f"Idea with id '{idea_id}' was not found.")
        return idea

    def list_ideas(self) -> List[Idea]:
        return self._store.list()

    def change_status(self, idea_id: str, status: str) -> Idea:
        idea = self.get_idea(idea_id)
        normalized = (status or "").strip().lower()

        if normalized not in VALID_STATUSES:
            raise ValueError(
                f"Invalid idea status '{status}'. Supported statuses: {sorted(VALID_STATUSES)}"
            )

        self._store.update_status(idea_id, normalized)
        idea.status = normalized
        return idea
