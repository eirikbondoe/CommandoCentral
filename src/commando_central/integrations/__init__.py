__all__ = ["CheckResult", "missing_required_env_vars", "run_connection_checks"]


def __getattr__(name: str):
    if name in __all__:
        from . import connectivity

        return getattr(connectivity, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
