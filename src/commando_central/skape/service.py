from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import Idea, Project, Task, VALID_STATUSES, VALID_TASK_STATUSES


class IdeaNotFoundError(KeyError):
    """Raised when an idea cannot be found in the service."""


class ProjectNotFoundError(KeyError):
    """Raised when a project cannot be found in the service."""


class TaskNotFoundError(KeyError):
    """Raised when a task cannot be found in the service."""


class SkapeStore(Protocol):
    def save_idea(self, idea: Idea) -> None: ...

    def get_idea(self, idea_id: str) -> Idea | None: ...

    def list_ideas(self) -> list[Idea]: ...

    def update_idea_status(self, idea_id: str, status: str) -> None: ...

    def save_project(self, project: Project) -> None: ...

    def get_project(self, project_id: str) -> Project | None: ...

    def list_projects(self) -> list[Project]: ...

    def update_project_status(self, project_id: str, status: str) -> None: ...

    def save_task(self, task: Task) -> None: ...

    def get_task(self, task_id: str) -> Task | None: ...

    def list_tasks(self, project_id: str | None = None) -> list[Task]: ...

    def update_task_status(self, task_id: str, status: str) -> None: ...


class InMemorySkapeStore:
    def __init__(self) -> None:
        self._ideas: dict[str, Idea] = {}
        self._projects: dict[str, Project] = {}
        self._tasks: dict[str, Task] = {}

    def save_idea(self, idea: Idea) -> None:
        self._ideas[idea.id] = idea

    def get_idea(self, idea_id: str) -> Idea | None:
        return self._ideas.get(idea_id)

    def list_ideas(self) -> list[Idea]:
        return list(self._ideas.values())

    def update_idea_status(self, idea_id: str, status: str) -> None:
        self._ideas[idea_id].status = status

    def save_project(self, project: Project) -> None:
        self._projects[project.id] = project

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_projects(self) -> list[Project]:
        return list(self._projects.values())

    def update_project_status(self, project_id: str, status: str) -> None:
        self._projects[project_id].status = status

    def save_task(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        if project_id is None:
            return list(self._tasks.values())
        return [task for task in self._tasks.values() if task.project_id == project_id]

    def update_task_status(self, task_id: str, status: str) -> None:
        self._tasks[task_id].status = status


class SQLiteSkapeStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
                """
            )
            connection.commit()

    @staticmethod
    def _normalize_created_at(value: str) -> datetime:
        created_at = datetime.fromisoformat(value)
        if created_at.tzinfo is None:
            return created_at.replace(tzinfo=timezone.utc)
        return created_at

    def _fetch_one(self, query: str, params: tuple[str, ...]) -> sqlite3.Row | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(query, params).fetchone()

    def _fetch_all(self, query: str, params: tuple[str, ...] = ()) -> list[sqlite3.Row]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(query, params).fetchall()

    def save_idea(self, idea: Idea) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO ideas (id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (idea.id, idea.title, idea.description, idea.status, idea.created_at.isoformat()),
            )
            connection.commit()

    def get_idea(self, idea_id: str) -> Idea | None:
        row = self._fetch_one(
            "SELECT id, title, description, status, created_at FROM ideas WHERE id = ?",
            (idea_id,),
        )
        if row is None:
            return None
        return Idea(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=self._normalize_created_at(row["created_at"]),
        )

    def list_ideas(self) -> list[Idea]:
        rows = self._fetch_all(
            "SELECT id, title, description, status, created_at FROM ideas ORDER BY created_at ASC, id ASC"
        )
        return [
            Idea(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                created_at=self._normalize_created_at(row["created_at"]),
            )
            for row in rows
        ]

    def update_idea_status(self, idea_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE ideas SET status = ? WHERE id = ?", (status, idea_id))
            connection.commit()

    def save_project(self, project: Project) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO projects (id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    project.id,
                    project.title,
                    project.description,
                    project.status,
                    project.created_at.isoformat(),
                ),
            )
            connection.commit()

    def get_project(self, project_id: str) -> Project | None:
        row = self._fetch_one(
            "SELECT id, title, description, status, created_at FROM projects WHERE id = ?",
            (project_id,),
        )
        if row is None:
            return None
        return Project(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=self._normalize_created_at(row["created_at"]),
        )

    def list_projects(self) -> list[Project]:
        rows = self._fetch_all(
            "SELECT id, title, description, status, created_at FROM projects ORDER BY created_at ASC, id ASC"
        )
        return [
            Project(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                created_at=self._normalize_created_at(row["created_at"]),
            )
            for row in rows
        ]

    def update_project_status(self, project_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
            connection.commit()

    def save_task(self, task: Task) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (id, project_id, title, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.project_id,
                    task.title,
                    task.description,
                    task.status,
                    task.created_at.isoformat(),
                ),
            )
            connection.commit()

    def get_task(self, task_id: str) -> Task | None:
        row = self._fetch_one(
            "SELECT id, project_id, title, description, status, created_at FROM tasks WHERE id = ?",
            (task_id,),
        )
        if row is None:
            return None
        return Task(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=self._normalize_created_at(row["created_at"]),
        )

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        if project_id is None:
            rows = self._fetch_all(
                """
                SELECT id, project_id, title, description, status, created_at
                FROM tasks
                ORDER BY created_at ASC, id ASC
                """
            )
        else:
            rows = self._fetch_all(
                """
                SELECT id, project_id, title, description, status, created_at
                FROM tasks
                WHERE project_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            )
        return [
            Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                created_at=self._normalize_created_at(row["created_at"]),
            )
            for row in rows
        ]

    def update_task_status(self, task_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
            connection.commit()


class SkapeService:
    def __init__(self, *, db_path: str | None = None, store: SkapeStore | None = None) -> None:
        if db_path and store is not None:
            raise ValueError("Use either db_path or store, not both.")
        self._store = store or (SQLiteSkapeStore(db_path) if db_path else InMemorySkapeStore())

    def create_idea(self, title: str, description: str = "") -> Idea:
        idea = Idea(title=title, description=description)
        self._store.save_idea(idea)
        return idea

    def get_idea(self, idea_id: str) -> Idea:
        idea = self._store.get_idea(idea_id)
        if idea is None:
            raise IdeaNotFoundError(f"Idea with id '{idea_id}' was not found.")
        return idea

    def list_ideas(self) -> list[Idea]:
        return self._store.list_ideas()

    def change_status(self, idea_id: str, status: str) -> Idea:
        idea = self.get_idea(idea_id)
        normalized = (status or "").strip().lower()

        if normalized not in VALID_STATUSES:
            raise ValueError(
                f"Invalid idea status '{status}'. Supported statuses: {sorted(VALID_STATUSES)}"
            )

        self._store.update_idea_status(idea_id, normalized)
        idea.status = normalized
        return idea

    def create_project(self, title: str, description: str = "") -> Project:
        project = Project(title=title, description=description)
        self._store.save_project(project)
        return project

    def get_project(self, project_id: str) -> Project:
        project = self._store.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with id '{project_id}' was not found.")
        return project

    def list_projects(self) -> list[Project]:
        return self._store.list_projects()

    def change_project_status(self, project_id: str, status: str) -> Project:
        project = self.get_project(project_id)
        normalized = (status or "").strip().lower()
        if normalized not in VALID_STATUSES:
            raise ValueError(
                f"Invalid project status '{status}'. Supported statuses: {sorted(VALID_STATUSES)}"
            )
        self._store.update_project_status(project_id, normalized)
        project.status = normalized
        return project

    def create_task(self, project_id: str, title: str, description: str = "") -> Task:
        project = self._store.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with id '{project_id}' was not found.")

        task = Task(project_id=project.id, title=title, description=description)
        self._store.save_task(task)
        return task

    def get_task(self, task_id: str) -> Task:
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task with id '{task_id}' was not found.")
        return task

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        if project_id is not None:
            project = self._store.get_project(project_id)
            if project is None:
                raise ProjectNotFoundError(f"Project with id '{project_id}' was not found.")
        return self._store.list_tasks(project_id)

    def change_task_status(self, task_id: str, status: str) -> Task:
        task = self.get_task(task_id)
        normalized = (status or "").strip().lower()
        if normalized not in VALID_TASK_STATUSES:
            raise ValueError(
                f"Invalid task status '{status}'. Supported statuses: {sorted(VALID_TASK_STATUSES)}"
            )
        self._store.update_task_status(task_id, normalized)
        task.status = normalized
        return task
