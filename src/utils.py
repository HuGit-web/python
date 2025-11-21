from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory (two levels up from this file)."""
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Return the `data/` directory path under project root and ensure it exists."""
    p = get_project_root() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p
