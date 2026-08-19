from __future__ import annotations

import os
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RITU_ROOT = Path(os.environ.get("RITU_POWERHOUSE_ROOT", REPO_ROOT.parent / "Powerhouse")).resolve()
PROJECTS_ROOT = RITU_ROOT / "projects"
SYSTEM_ROOT = RITU_ROOT / ".ritu"
UPLOAD_ROOT = RITU_ROOT / "uploads"
DATABASE_PATH = SYSTEM_ROOT / "ritu_company.db"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_FAST_MODEL = os.environ.get("RITU_FAST_MODEL", "qwen2.5:7b")
OLLAMA_DEEP_MODEL = os.environ.get("RITU_DEEP_MODEL", "qwen2.5:14b")
OLLAMA_MODEL = OLLAMA_FAST_MODEL
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_GENERATED_FILE_BYTES = 2 * 1024 * 1024
ALLOWED_GENERATED_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".toml",
    ".ini",
    ".html",
    ".css",
    ".js",
}


def ensure_layout() -> None:
    for path in (RITU_ROOT, PROJECTS_ROOT, SYSTEM_ROOT, UPLOAD_ROOT):
        path.mkdir(parents=True, exist_ok=True)


def slugify(value: str, fallback: str = "project") -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return value[:72] or fallback


def safe_filename(value: str, fallback: str = "reference") -> str:
    name = Path(value).name
    stem = re.sub(r"[^a-zA-Z0-9._ -]+", "_", name).strip(" .")
    return stem[:140] or fallback


def confined_path(root: Path, relative: str | Path) -> Path:
    candidate = (root / relative).resolve()
    root = root.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Path leaves the allowed Powerhouse workspace.")
    return candidate
