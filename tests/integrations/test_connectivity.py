from commando_central import integrations
from commando_central.integrations import connectivity
from commando_central.integrations.connectivity import CheckResult, missing_required_env_vars


def test_integrations_package_re_exports_connectivity_helpers():
    assert integrations.CheckResult is CheckResult
    assert integrations.missing_required_env_vars is missing_required_env_vars


def test_missing_required_env_vars_returns_all_missing():
    missing = missing_required_env_vars({})

    assert missing == [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
    ]


def test_missing_required_env_vars_ignores_set_values():
    missing = missing_required_env_vars(
        {
            "NOTION_TOKEN": "secret_abc",
            "NOTION_DATABASE_ID": "db-id",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_ANON_KEY": "anon-key",
        }
    )

    assert missing == []


def test_missing_required_env_vars_treats_whitespace_as_missing():
    missing = missing_required_env_vars(
        {
            "NOTION_TOKEN": "secret_abc",
            "NOTION_DATABASE_ID": "   ",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_ANON_KEY": "anon-key",
        }
    )

    assert missing == ["NOTION_DATABASE_ID"]


def test_main_returns_non_zero_when_required_env_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        connectivity,
        "missing_required_env_vars",
        lambda environ=None: ["NOTION_DATABASE_ID"],
    )
    monkeypatch.setattr(
        connectivity,
        "run_connection_checks",
        lambda environ=None, timeout=10: [
            CheckResult("Notion", True, "Tilkobling OK."),
            CheckResult("GitHub", True, "Tilkobling OK (uten token)."),
            CheckResult("Supabase", True, "Tilkobling OK."),
        ],
    )

    exit_code = connectivity.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "NOTION_DATABASE_ID" in captured.out
