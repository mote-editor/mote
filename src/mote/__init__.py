from __future__ import annotations

from pathlib import Path


def _read_version_from_pyproject() -> str:
	pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
	try:
		data = pyproject_path.read_bytes()
	except OSError:
		return "unknown"

	try:
		import tomllib  # Python 3.11+
	except ModuleNotFoundError:  # pragma: no cover
		try:
			import tomli as tomllib
		except ModuleNotFoundError:
			return "unknown"

	try:
		parsed = tomllib.loads(data.decode("utf-8"))
		return parsed.get("project", {}).get("version", "unknown")
	except Exception:
		return "unknown"


__version__ = _read_version_from_pyproject()
