from __future__ import annotations

import json
from importlib.resources import files

SUPPORTED_LOCALES = ("en", "no")


def load_locale(locale: str) -> dict[str, str]:
    normalized = (locale or "").strip().lower()
    if normalized not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale '{locale}'. Supported locales: {SUPPORTED_LOCALES}")

    locale_path = files("commando_central.i18n.locales") / f"{normalized}.json"
    return json.loads(locale_path.read_text(encoding="utf-8"))
