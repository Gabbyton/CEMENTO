from importlib import resources
from pathlib import Path


def get_default_path(rel_path: str | Path) -> Path:
    try:
        return resources.files("cemento.data") / rel_path
    except (ImportError, FileNotFoundError, ModuleNotFoundError):
        return Path(__file__).parent / "data" / rel_path


def get_default_defaults_folder() -> Path:
    return get_default_path("defaults")


def get_default_references_folder() -> Path:
    return get_default_path("references")


def get_default_prefixes_file() -> Path:
    return get_default_path("default_prefixes.json")
