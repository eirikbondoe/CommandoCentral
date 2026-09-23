from __future__ import annotations

from typing import List

from .models import Idea, VALID_STATUSES


class IdeaNotFoundError(KeyError):
    """Raised when an idea cannot be found in the service."""


class SkapeService:
    def __init__(self) -> None:
        self._ideas: dict[str, Idea] = {}

    def create_idea(self, title: str, description: str = "") -> Idea:
        idea = Idea(title=title, description=description)
        self._ideas[idea.id] = idea
        return idea

    def get_idea(self, idea_id: str) -> Idea:
        idea = self._ideas.get(idea_id)
        if idea is None:
            raise IdeaNotFoundError(f"Idea with id '{idea_id}' was not found.")
        return idea

    def list_ideas(self) -> List[Idea]:
        return list(self._ideas.values())

    def change_status(self, idea_id: str, status: str) -> Idea:
        idea = self.get_idea(idea_id)
        normalized = (status or "").strip().lower()

        if normalized not in VALID_STATUSES:
            raise ValueError(
                f"Invalid idea status '{status}'. Supported statuses: {sorted(VALID_STATUSES)}"
            )

        idea.status = normalized
        return idea
