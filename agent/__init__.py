# Agent package init

from .config import Settings

__all__ = ["Settings", "__version__"]

# Best-effort version detection when installed as a package; fallback for dev
try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        # Try common distribution names; fallback if not installed
        for _name in ("flashloan-ai-agent", "flashloan_ai_agent", "agent"):
            try:
                __version__ = _pkg_version(_name)
                break
            except PackageNotFoundError:
                continue
        else:
            __version__ = "0.1.0"
    except Exception:
        __version__ = "0.1.0"
except Exception:
    __version__ = "0.1.0"
