"""Kortana core package."""

from importlib.metadata import version

__all__ = ["__version__"]


def __getattr__(name: str):
    if name == "__version__":
        try:
            return version("kortana")
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise AttributeError("kortana package metadata is unavailable") from exc
    raise AttributeError(name)
