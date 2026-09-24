from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_env_example_contains_required_keys():
    env_text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    for key in (
        "NOTION_API_KEY",
        "NOTION_DATABASE_ID",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "NOTION_SYNC_OWNER_ID",
    ):
        assert f"{key}=" in env_text


def test_supabase_config_exposes_notion_sync_configuration():
    config = tomllib.loads((REPO_ROOT / "supabase" / "config.toml").read_text(encoding="utf-8"))

    assert config["project_id"] == "commandocentral"
    assert config["functions"]["notion-sync"]["verify_jwt"] is False


def test_migration_files_exist_for_core_framework_and_backup():
    migrations = REPO_ROOT / "supabase" / "migrations"

    assert (migrations / "20260924000100_create_core_framework.sql").exists()
    assert (migrations / "20260924000200_create_notion_pages_and_backup_audit.sql").exists()
