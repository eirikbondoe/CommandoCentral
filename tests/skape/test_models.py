import pytest

from commando_central.skape.models import Idea, Project, Task


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


def test_project_is_created_with_default_status():
    project = Project(title="Commando MVP", description="Core delivery")

    assert project.title == "Commando MVP"
    assert project.description == "Core delivery"
    assert project.status == "draft"
    assert project.id


def test_project_title_cannot_be_empty():
    with pytest.raises(ValueError, match="Project title cannot be empty"):
        Project(title=" ")


def test_task_is_created_with_default_status():
    task = Task(project_id="project-1", title="Create backlog", description="Seed initial tasks")

    assert task.project_id == "project-1"
    assert task.title == "Create backlog"
    assert task.description == "Seed initial tasks"
    assert task.status == "todo"
    assert task.id


def test_task_requires_project_id():
    with pytest.raises(ValueError, match="Task project_id cannot be empty"):
        Task(project_id=" ", title="Missing project")


def test_task_rejects_invalid_status():
    with pytest.raises(ValueError, match="Invalid task status"):
        Task(project_id="project-1", title="Build", status="draft")
