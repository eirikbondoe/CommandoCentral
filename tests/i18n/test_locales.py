import json
from pathlib import Path

import pytest

from commando_central.i18n import SUPPORTED_LOCALES, load_locale


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_supported_locales_are_stable():
    assert SUPPORTED_LOCALES == ("en", "no")


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_locale_files_are_valid_json_and_contain_core_keys(locale):
    path = REPO_ROOT / "src" / "commando_central" / "i18n" / "locales" / f"{locale}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["ideas.title"]
    assert payload["decisions.title"]
    assert payload["products.title"]


def test_load_locale_rejects_unsupported_locale():
    with pytest.raises(ValueError, match="Unsupported locale"):
        load_locale("fr")
