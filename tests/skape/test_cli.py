from io import StringIO

from commando_central.skape.cli import SkapeCli
from commando_central.skape.service import SkapeService


def test_cli_can_create_list_and_update_status():
    service = SkapeService()
    stdout = StringIO()
    shell = SkapeCli(service=service, stdout=stdout)

    shell.onecmd('create "Build launch checklist" -d "Release prep"')
    created = service.list_ideas()
    assert len(created) == 1
    idea_id = created[0].id

    shell.onecmd("list")
    shell.onecmd(f"status {idea_id} active")

    assert service.get_idea(idea_id).status == "active"
    output = stdout.getvalue()
    assert "Created:" in output
    assert f"{idea_id} | draft | Build launch checklist" in output
    assert f"Updated: {idea_id} [active] Build launch checklist" in output


def test_cli_returns_not_found_error_when_updating_unknown_idea():
    stdout = StringIO()
    shell = SkapeCli(service=SkapeService(), stdout=stdout)

    shell.onecmd("status does-not-exist active")

    assert "does-not-exist" in stdout.getvalue()


def test_cli_can_manage_projects_and_tasks():
    service = SkapeService()
    stdout = StringIO()
    shell = SkapeCli(service=service, stdout=stdout)

    shell.onecmd('project_create "Delivery project" -d "Phase 1"')
    project = service.list_projects()[0]
    shell.onecmd(f'task_create {project.id} "Write docs" -d "Outline scope"')
    task = service.list_tasks(project.id)[0]
    shell.onecmd(f"task_status {task.id} in_progress")
    shell.onecmd(f"task_list --project-id {project.id}")

    assert service.get_task(task.id).status == "in_progress"
    output = stdout.getvalue()
    assert "Project created:" in output
    assert "Task created:" in output
    assert "Task updated:" in output
