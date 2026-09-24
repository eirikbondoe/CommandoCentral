from __future__ import annotations

import argparse
import cmd
import shlex
from typing import TextIO

from .service import IdeaNotFoundError, ProjectNotFoundError, SkapeService, TaskNotFoundError


class SkapeCli(cmd.Cmd):
    intro = "Skape CLI. Skriv 'help' for kommandoer."
    prompt = "skape> "

    def __init__(self, service: SkapeService | None = None, *, stdout: TextIO | None = None) -> None:
        super().__init__(stdout=stdout)
        self.service = service or SkapeService()

    def emptyline(self) -> None:
        return

    def _parse(self, parser: argparse.ArgumentParser, arg: str) -> argparse.Namespace | None:
        try:
            tokens = shlex.split(arg)
        except ValueError as error:
            print(f"Ugyldig argumentformat: {error}", file=self.stdout)
            return None

        try:
            return parser.parse_args(tokens)
        except SystemExit:
            return None

    def do_create(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="create")
        parser.add_argument("title")
        parser.add_argument("-d", "--description", default="")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        idea = self.service.create_idea(parsed.title, parsed.description)
        print(f"Created: {idea.id} [{idea.status}] {idea.title}", file=self.stdout)

    def do_list(self, arg: str) -> None:
        if arg.strip():
            print("Bruk: list", file=self.stdout)
            return

        ideas = self.service.list_ideas()
        if not ideas:
            print("No ideas.", file=self.stdout)
            return

        for idea in ideas:
            print(f"{idea.id} | {idea.status} | {idea.title}", file=self.stdout)

    def do_status(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="status")
        parser.add_argument("idea_id")
        parser.add_argument("status")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        try:
            idea = self.service.change_status(parsed.idea_id, parsed.status)
        except (IdeaNotFoundError, ValueError) as error:
            print(error, file=self.stdout)
            return

        print(f"Updated: {idea.id} [{idea.status}] {idea.title}", file=self.stdout)

    def do_project_create(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="project_create")
        parser.add_argument("title")
        parser.add_argument("-d", "--description", default="")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        project = self.service.create_project(parsed.title, parsed.description)
        print(f"Project created: {project.id} [{project.status}] {project.title}", file=self.stdout)

    def do_project_list(self, arg: str) -> None:
        if arg.strip():
            print("Bruk: project_list", file=self.stdout)
            return

        projects = self.service.list_projects()
        if not projects:
            print("No projects.", file=self.stdout)
            return

        for project in projects:
            print(f"{project.id} | {project.status} | {project.title}", file=self.stdout)

    def do_project_status(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="project_status")
        parser.add_argument("project_id")
        parser.add_argument("status")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        try:
            project = self.service.change_project_status(parsed.project_id, parsed.status)
        except (ProjectNotFoundError, ValueError) as error:
            print(error, file=self.stdout)
            return

        print(f"Project updated: {project.id} [{project.status}] {project.title}", file=self.stdout)

    def do_task_create(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="task_create")
        parser.add_argument("project_id")
        parser.add_argument("title")
        parser.add_argument("-d", "--description", default="")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        try:
            task = self.service.create_task(parsed.project_id, parsed.title, parsed.description)
        except (ProjectNotFoundError, ValueError) as error:
            print(error, file=self.stdout)
            return

        print(
            f"Task created: {task.id} [{task.status}] {task.title} (project: {task.project_id})",
            file=self.stdout,
        )

    def do_task_list(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="task_list")
        parser.add_argument("-p", "--project-id", default=None)
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        try:
            tasks = self.service.list_tasks(parsed.project_id)
        except ProjectNotFoundError as error:
            print(error, file=self.stdout)
            return

        if not tasks:
            print("No tasks.", file=self.stdout)
            return

        for task in tasks:
            print(f"{task.id} | {task.status} | {task.title} | project={task.project_id}", file=self.stdout)

    def do_task_status(self, arg: str) -> None:
        parser = argparse.ArgumentParser(prog="task_status")
        parser.add_argument("task_id")
        parser.add_argument("status")
        parsed = self._parse(parser, arg)
        if parsed is None:
            return

        try:
            task = self.service.change_task_status(parsed.task_id, parsed.status)
        except (TaskNotFoundError, ValueError) as error:
            print(error, file=self.stdout)
            return

        print(f"Task updated: {task.id} [{task.status}] {task.title}", file=self.stdout)

    def do_exit(self, arg: str) -> bool:
        return True

    def do_quit(self, arg: str) -> bool:
        return True

    def do_EOF(self, arg: str) -> bool:  # noqa: N802
        print(file=self.stdout)
        return True


def run_cli(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    *,
    db_path: str = "skape.db",
) -> int:
    shell = SkapeCli(service=SkapeService(db_path=db_path), stdout=stdout)
    if stdin is not None:
        shell.stdin = stdin
        shell.use_rawinput = False
    shell.cmdloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skape CLI")
    parser.add_argument("--db", default="skape.db", help="Path to SQLite database file.")
    args = parser.parse_args()
    return run_cli(db_path=args.db)


if __name__ == "__main__":
    raise SystemExit(main())
