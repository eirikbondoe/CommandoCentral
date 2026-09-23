import pytest

from commando_central.skape.models import Idea


def test_idea_is_created_with_default_status():
    idea = Idea(title="Build a better workflow")

    assert idea.title == "Build a better workflow"
    assert idea.description == ""
    assert idea.status == "draft"
    assert idea.id


def test_idea_title_cannot_be_empty():
    with pytest.raises(ValueError, match="Idea title cannot be empty"):
        Idea(title="   ")


def test_idea_rejects_invalid_status():
    with pytest.raises(ValueError, match="Invalid idea status"):
        Idea(title="Prototype", status="in_progress")


def test_idea_trims_whitespace_from_title_and_description():
    idea = Idea(title="  Launch feature  ", description="  Needs validation  ")

    assert idea.title == "Launch feature"
    assert idea.description == "Needs validation"
