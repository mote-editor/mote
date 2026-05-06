from __future__ import annotations

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("mote")
    except PackageNotFoundError:
        __version__ = "unknown"
except ImportError:
    __version__ = "unknown"
