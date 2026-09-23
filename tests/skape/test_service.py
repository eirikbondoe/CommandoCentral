import pytest

from commando_central.skape.models import Idea
from commando_central.skape.service import IdeaNotFoundError, SkapeService


def test_service_creates_idea_with_defaults():
    service = SkapeService()

    idea = service.create_idea("Plan the MVP")

    assert idea.title == "Plan the MVP"
    assert idea.status == "draft"
    assert idea.id in {item.id for item in service.list_ideas()}


def test_service_lists_all_ideas():
    service = SkapeService()
    service.create_idea("Idea 1")
    service.create_idea("Idea 2")

    ideas = service.list_ideas()

    assert len(ideas) == 2
    assert {idea.title for idea in ideas} == {"Idea 1", "Idea 2"}


def test_service_changes_status():
    service = SkapeService()
    idea = service.create_idea("Ship the first release")

    updated = service.change_status(idea.id, "active")

    assert updated.status == "active"
    assert service.get_idea(idea.id).status == "active"


def test_service_normalizes_status_on_change():
    service = SkapeService()
    idea = service.create_idea("Ship the second release")

    updated = service.change_status(idea.id, "  COMPLETED  ")

    assert updated.status == "completed"


def test_service_rejects_invalid_status():
    service = SkapeService()
    idea = service.create_idea("Refine roadmap")

    with pytest.raises(ValueError, match="Invalid idea status"):
        service.change_status(idea.id, "review")


def test_service_raises_for_missing_idea():
    service = SkapeService()

    with pytest.raises(IdeaNotFoundError, match="was not found"):
        service.get_idea("missing-id")


def test_service_can_create_idea_with_description():
    service = SkapeService()

    idea = service.create_idea("Document the process", "Start with a clear domain model.")

    assert idea.description == "Start with a clear domain model."
    assert isinstance(idea, Idea)
