import pytest

from commando_central.skape.service import IdeaNotFoundError, SkapeService


def test_service_in_memory_create_and_get():
    service = SkapeService()
    created = service.create_idea("Plan release", "Coordinate tasks")

    fetched = service.get_idea(created.id)
    assert fetched.id == created.id
    assert fetched.title == "Plan release"
    assert fetched.description == "Coordinate tasks"
    assert fetched.status == "draft"


def test_service_change_status_rejects_invalid_status():
    service = SkapeService()
    created = service.create_idea("Prototype")

    with pytest.raises(ValueError, match="Invalid idea status"):
        service.change_status(created.id, "in_progress")


def test_service_raises_for_missing_idea():
    service = SkapeService()
    with pytest.raises(IdeaNotFoundError, match="was not found"):
        service.get_idea("missing")


def test_service_persists_ideas_in_sqlite(tmp_path):
    db_file = tmp_path / "ideas.db"
    first = SkapeService(db_path=str(db_file))
    created = first.create_idea("Persistent idea", "Store me")

    second = SkapeService(db_path=str(db_file))
    listed = second.list_ideas()
    assert len(listed) == 1
    assert listed[0].id == created.id
    assert listed[0].title == "Persistent idea"


def test_service_persists_status_updates_in_sqlite(tmp_path):
    db_file = tmp_path / "ideas.db"
    writer = SkapeService(db_path=str(db_file))
    created = writer.create_idea("Move forward")
    writer.change_status(created.id, "active")

    reader = SkapeService(db_path=str(db_file))
    reloaded = reader.get_idea(created.id)
    assert reloaded.status == "active"
