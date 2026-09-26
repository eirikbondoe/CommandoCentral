# CommandoCentral

CommandoCentral is a project focused on building a practical, extensible system around the Skape concept. The current MVP establishes the core idea domain and test-first workflow needed to grow the platform safely.

## Language and internationalization

CommandoCentral is built as a multilingual application from the start.
Our goal is **fullspråklighet**: the system should be usable, understandable, and extendable across languages without language becoming a technical limitation.

Language support is therefore part of the architecture, not an afterthought.

### Principles

- all user-facing text should be translatable
- the system should support Unicode and different writing systems
- language should be selectable per user or context
- dates, numbers, and other formats should be localizable
- missing translations should be handled safely with fallbacks
- new features should be evaluated against the goal of fullspråklighet

### Architecture rule

No new functionality should be introduced in a way that locks the system to a single language.

This means:

- no hardcoded UI text in domain logic
- translations should stay separate from code and business rules
- data models and APIs must tolerate multilingual content
- default behavior should remain language-agnostic, with a clear fallback strategy

## Skape MVP

Skape currently includes a minimal domain model and service layer for managing ideas:

- create ideas
- create projects and tasks
- validate titles
- track creation timestamps
- maintain supported statuses
- list and update ideas
- list and update projects and tasks
- persist ideas, projects and tasks in SQLite
- raise clear errors for invalid input and missing ideas

## Project structure

```text
CommandoCentral/
├── .github/
│   └── workflows/
│       └── tests.yml
├── .env.example
├── README.md
├── pyproject.toml
├── src/
│   └── commando_central/
│       ├── integrations/
│       │   ├── __init__.py
│       │   └── connectivity.py
│       └── skape/
│           ├── __init__.py
│           ├── cli.py
│           ├── models.py
│           └── service.py
├── tests/
│   ├── integrations/
│   │   └── test_connectivity.py
│   └── skape/
│       ├── test_cli.py
│       ├── test_models.py
│       └── test_service.py
└── .gitignore
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Integrations bootstrap (Notion, GitHub, Supabase)

1. Copy `.env.example` to `.env` and fill in real values.
2. Export the same variables in your shell/session.
3. Run connection checks:

```bash
python -m commando_central.integrations.connectivity
```

Required variables:

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Optional:

- `GITHUB_TOKEN` (recommended for higher API rate limits)

## Running tests

```bash
pytest
```

## CLI (next step implemented)

Start the interactive Skape CLI (uses `skape.db` by default):

```bash
python -m commando_central.skape.cli
```

or after installation:

```bash
skape
```

use a custom SQLite path:

```bash
skape --db ./data/skape.db
```

Available commands:

- `create "<title>" -d "<description>"`
- `list`
- `status <idea_id> <draft|active|completed|archived>`
- `project_create "<title>" -d "<description>"`
- `project_list`
- `project_status <project_id> <draft|active|completed|archived>`
- `task_create <project_id> "<title>" -d "<description>"`
- `task_list [--project-id <project_id>]`
- `task_status <task_id> <todo|in_progress|completed|blocked>`
- `exit` / `quit`

## Current scope

This MVP deliberately stays small and intentionally does not include:

- web UI
- authentication
- external APIs
- project orchestration beyond the idea domain

## Next possible steps

1. add deeper integration tests around persisted workflows
2. connect the domain to the rest of CommandoCentral
3. expose the domain via API or orchestration layer
