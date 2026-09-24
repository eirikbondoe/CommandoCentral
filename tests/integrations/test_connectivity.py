from commando_central.integrations.connectivity import missing_required_env_vars


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
