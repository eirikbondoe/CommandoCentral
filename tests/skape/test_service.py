import pytest

from commando_central.skape.service import (
    IdeaNotFoundError,
    ProjectNotFoundError,
    SkapeService,
    TaskNotFoundError,
)


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


def test_service_create_project_and_task_in_memory():
    service = SkapeService()
    project = service.create_project("Project A", "Main initiative")
    task = service.create_task(project.id, "Task 1", "First task")

    assert service.get_project(project.id).title == "Project A"
    assert service.get_task(task.id).project_id == project.id
    assert service.list_tasks(project.id)[0].id == task.id


def test_service_rejects_task_creation_for_missing_project():
    service = SkapeService()
    with pytest.raises(ProjectNotFoundError, match="was not found"):
        service.create_task("missing", "Task")


def test_service_change_task_status_rejects_invalid_status():
    service = SkapeService()
    project = service.create_project("Project B")
    task = service.create_task(project.id, "Task B")

    with pytest.raises(ValueError, match="Invalid task status"):
        service.change_task_status(task.id, "active")


def test_service_raises_for_missing_task():
    service = SkapeService()
    with pytest.raises(TaskNotFoundError, match="was not found"):
        service.get_task("missing-task")


def test_service_persists_projects_and_tasks_in_sqlite(tmp_path):
    db_file = tmp_path / "skape.db"
    writer = SkapeService(db_path=str(db_file))
    project = writer.create_project("Persistent project")
    task = writer.create_task(project.id, "Persistent task")
    writer.change_task_status(task.id, "in_progress")

    reader = SkapeService(db_path=str(db_file))
    reloaded_project = reader.get_project(project.id)
    reloaded_task = reader.get_task(task.id)

    assert reloaded_project.title == "Persistent project"
    assert reloaded_task.project_id == project.id
    assert reloaded_task.status == "in_progress"
