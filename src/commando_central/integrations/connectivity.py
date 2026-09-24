from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Mapping

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "NOTION_TOKEN",
    "NOTION_DATABASE_ID",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
)


@dataclass(slots=True)
class CheckResult:
    service: str
    ok: bool
    message: str


def missing_required_env_vars(environ: Mapping[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    return [name for name in REQUIRED_ENV_VARS if not (env.get(name) or "").strip()]


def _http_get_json(
    url: str, *, headers: Mapping[str, str] | None = None, timeout: int = 10
) -> tuple[int, dict | None]:
    request = urllib.request.Request(url, headers=dict(headers or {}))

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError:
            payload = None
        return error.code, payload
    except urllib.error.URLError as error:
        return 0, {"message": str(error.reason)}


def _check_notion(token: str, timeout: int) -> CheckResult:
    if not token.strip():
        return CheckResult("Notion", False, "NOTION_TOKEN mangler.")

    status, payload = _http_get_json(
        "https://api.notion.com/v1/users/me",
        headers={
            "Authorization": " ".join(("Bearer", token)),
            "Notion-Version": "2022-06-28",
        },
        timeout=timeout,
    )

    if status == 200:
        return CheckResult("Notion", True, "Tilkobling OK.")

    details = (payload or {}).get("message", "ukjent feil")
    return CheckResult("Notion", False, f"Feilet (HTTP {status}): {details}")


def _check_github(token: str, timeout: int) -> CheckResult:
    headers = {"Accept": "application/vnd.github+json"}
    message_suffix = "uten token"
    if token.strip():
        headers["Authorization"] = " ".join(("Bearer", token))
        message_suffix = "med token"

    status, _ = _http_get_json(
        "https://api.github.com/rate_limit",
        headers=headers,
        timeout=timeout,
    )

    if status == 200:
        return CheckResult("GitHub", True, f"Tilkobling OK ({message_suffix}).")

    return CheckResult("GitHub", False, f"Feilet (HTTP {status}).")


def _check_supabase(url: str, anon_key: str, timeout: int) -> CheckResult:
    if not url.strip():
        return CheckResult("Supabase", False, "SUPABASE_URL mangler.")
    if not anon_key.strip():
        return CheckResult("Supabase", False, "SUPABASE_ANON_KEY mangler.")

    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return CheckResult("Supabase", False, "SUPABASE_URL må starte med http:// eller https://.")

    normalized_url = url.strip().rstrip("/")
    status, payload = _http_get_json(
        f"{normalized_url}/auth/v1/settings",
        headers={
            "apikey": anon_key,
            "Authorization": " ".join(("Bearer", anon_key)),
        },
        timeout=timeout,
    )

    if status == 200:
        return CheckResult("Supabase", True, "Tilkobling OK.")

    details = (payload or {}).get("msg") or (payload or {}).get("message") or "ukjent feil"
    return CheckResult("Supabase", False, f"Feilet (HTTP {status}): {details}")


def run_connection_checks(environ: Mapping[str, str] | None = None, timeout: int = 10) -> list[CheckResult]:
    env = environ if environ is not None else os.environ
    return [
        _check_notion((env.get("NOTION_TOKEN") or "").strip(), timeout),
        _check_github((env.get("GITHUB_TOKEN") or "").strip(), timeout),
        _check_supabase(
            (env.get("SUPABASE_URL") or "").strip(),
            (env.get("SUPABASE_ANON_KEY") or "").strip(),
            timeout,
        ),
    ]


def main() -> int:
    missing = missing_required_env_vars()
    if missing:
        print("Mangler miljøvariabler:", ", ".join(missing))

    results = run_connection_checks()
    for result in results:
        status = "OK" if result.ok else "FEIL"
        print(f"[{status}] {result.service}: {result.message}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
