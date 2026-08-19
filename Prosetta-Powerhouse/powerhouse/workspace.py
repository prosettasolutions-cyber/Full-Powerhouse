from __future__ import annotations

import base64
import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import (
    ALLOWED_GENERATED_SUFFIXES,
    MAX_GENERATED_FILE_BYTES,
    MAX_UPLOAD_BYTES,
    PROJECTS_ROOT,
    REPO_ROOT,
    RITU_ROOT,
    UPLOAD_ROOT,
    confined_path,
    safe_filename,
)
from .store import CompanyStore


class PowerhouseWorkspace:
    def __init__(self, store: CompanyStore):
        self.store = store

    def project_root(self, project: dict[str, Any]) -> Path:
        root = confined_path(PROJECTS_ROOT, project["slug"])
        root.mkdir(parents=True, exist_ok=True)
        (root / "references").mkdir(exist_ok=True)
        (root / ".history").mkdir(exist_ok=True)
        return root

    def initialize_project(self, project: dict[str, Any]) -> Path:
        root = self.project_root(project)
        readme = root / "README.md"
        if not readme.exists():
            content = (
                f"# {project['name']}\n\n"
                f"## Objective\n\n{project['objective']}\n\n"
                "## Operating notes\n\n"
                "This project is managed locally by Ritu. Generated files are versioned and audited.\n"
            )
            self.write_text(project, "README.md", content, summary="Project workspace initialized")
        return root

    def write_text(
        self,
        project: dict[str, Any],
        relative_path: str,
        content: str,
        task_id: str | None = None,
        summary: str = "",
    ) -> dict[str, Any]:
        root = self.project_root(project)
        target = confined_path(root, relative_path)
        if target.suffix.lower() not in ALLOWED_GENERATED_SUFFIXES:
            raise ValueError(f"File type is not allowed for autonomous creation: {target.suffix or 'none'}")
        payload = content.encode("utf-8")
        if len(payload) > MAX_GENERATED_FILE_BYTES:
            raise ValueError("Generated file exceeds the 2 MB safety limit.")

        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_bytes() if target.exists() else None
        if existing == payload:
            version_row = self.store.one(
                "SELECT MAX(version) AS version FROM artifacts WHERE project_id=? AND path=?",
                (project["id"], str(target.relative_to(root)).replace("\\", "/")),
            )
            return {
                "path": str(target),
                "relative_path": str(target.relative_to(root)).replace("\\", "/"),
                "version": int((version_row or {}).get("version") or 1),
                "unchanged": True,
            }

        version_row = self.store.one(
            "SELECT MAX(version) AS version FROM artifacts WHERE project_id=? AND path=?",
            (project["id"], str(target.relative_to(root)).replace("\\", "/")),
        )
        version = int((version_row or {}).get("version") or 0) + 1
        if existing is not None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            history_relative = f"{target.relative_to(root)}.{timestamp}.v{version - 1}.bak"
            history_target = confined_path(root / ".history", history_relative)
            history_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, history_target)

        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
            Path(temporary_name).replace(target)
        finally:
            if Path(temporary_name).exists():
                Path(temporary_name).unlink()

        relative = str(target.relative_to(root)).replace("\\", "/")
        digest = hashlib.sha256(payload).hexdigest()
        self.store.add_artifact(project["id"], task_id, relative, version, digest, summary)
        return {"path": str(target), "relative_path": relative, "version": version, "sha256": digest}

    def save_reference(
        self,
        project: dict[str, Any] | None,
        filename: str,
        encoded_data: str,
        media_type: str,
    ) -> dict[str, Any]:
        if "," in encoded_data:
            encoded_data = encoded_data.split(",", 1)[1]
        payload = base64.b64decode(encoded_data, validate=True)
        if not payload or len(payload) > MAX_UPLOAD_BYTES:
            raise ValueError("Reference must be between 1 byte and 20 MB.")

        name = safe_filename(filename)
        if project:
            root = self.project_root(project) / "references"
        else:
            root = UPLOAD_ROOT / "inbox"
        root.mkdir(parents=True, exist_ok=True)
        target = confined_path(root, name)
        if target.exists():
            digest_short = hashlib.sha256(payload).hexdigest()[:8]
            target = target.with_name(f"{target.stem}-{digest_short}{target.suffix}")
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        reference = self.store.add_reference(
            project["id"] if project else None,
            target.name,
            str(target),
            media_type or "application/octet-stream",
            digest,
        )
        return {**reference, "size": len(payload)}

    def project_file_index(self, project: dict[str, Any], limit: int = 80) -> list[str]:
        return [item["path"] for item in self.list_files("project", project, limit)]

    @staticmethod
    def _excluded_parts() -> set[str]:
        return {".git", ".history", "__pycache__", ".pytest_cache", "backups"}

    @staticmethod
    def clean_relative_path(relative_path: str) -> Path:
        normalized = Path(os.path.normpath(relative_path.replace("\\", "/")))
        if normalized.is_absolute() or ".." in normalized.parts or str(normalized) in {"", "."}:
            raise ValueError("A safe relative file path is required.")
        return normalized

    def scope_root(self, scope: str, project: dict[str, Any] | None = None) -> Path:
        if scope == "project":
            if not project:
                raise ValueError("A project is required for project files.")
            return self.project_root(project)
        if scope == "portal":
            return REPO_ROOT
        raise ValueError("File scope must be project or portal.")

    def list_files(
        self,
        scope: str,
        project: dict[str, Any] | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        root = self.scope_root(scope, project)
        rows: list[dict[str, Any]] = []
        excluded = self._excluded_parts()
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if any(part in excluded or part.startswith(".env") for part in relative.parts):
                continue
            if not path.is_file():
                continue
            stat = path.stat()
            rows.append(
                {
                    "scope": scope,
                    "project_id": project["id"] if project else None,
                    "path": str(relative).replace("\\", "/"),
                    "size": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "editable": path.suffix.lower() in ALLOWED_GENERATED_SUFFIXES,
                }
            )
            if len(rows) >= limit:
                break
        return rows

    def read_text_file(
        self,
        scope: str,
        relative_path: str,
        project: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        root = self.scope_root(scope, project)
        relative = self.clean_relative_path(relative_path)
        target = confined_path(root, str(relative))
        if any(part in self._excluded_parts() or part.startswith(".env") for part in relative.parts):
            raise ValueError("This internal path is not available to Ritu.")
        if not target.is_file():
            raise ValueError(f"File not found: {relative_path}")
        if target.suffix.lower() not in ALLOWED_GENERATED_SUFFIXES:
            raise ValueError("This file is stored but is not an editable text file.")
        if target.stat().st_size > MAX_GENERATED_FILE_BYTES:
            raise ValueError("File exceeds the 2 MB text interaction limit.")
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "scope": scope,
            "project_id": project["id"] if project else None,
            "path": str(relative).replace("\\", "/"),
            "content": content,
            "size": len(content.encode("utf-8")),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "verified": True,
        }

    def write_scoped_text(
        self,
        scope: str,
        relative_path: str,
        content: str,
        project: dict[str, Any] | None = None,
        summary: str = "",
    ) -> dict[str, Any]:
        if scope == "project":
            if not project:
                raise ValueError("A project is required for project files.")
            root = self.project_root(project)
            relative = self.clean_relative_path(relative_path)
            confined_path(root, str(relative))
            if any(part in self._excluded_parts() or part.startswith(".env") for part in relative.parts):
                raise ValueError("This internal path cannot be changed.")
            result = self.write_text(project, relative_path, content, summary=summary)
            verified = self.read_text_file(scope, relative_path, project)
            return {**result, **verified, "unchanged": bool(result.get("unchanged"))}

        root = self.scope_root(scope, project)
        relative = self.clean_relative_path(relative_path)
        target = confined_path(root, str(relative))
        if any(part in self._excluded_parts() or part.startswith(".env") for part in relative.parts):
            raise ValueError("This internal path cannot be changed.")
        if target.suffix.lower() not in ALLOWED_GENERATED_SUFFIXES:
            raise ValueError(f"File type is not allowed for portal editing: {target.suffix or 'none'}")
        payload = content.encode("utf-8")
        if len(payload) > MAX_GENERATED_FILE_BYTES:
            raise ValueError("File exceeds the 2 MB safety limit.")
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_bytes() if target.exists() else None
        if existing == payload:
            return {**self.read_text_file(scope, relative_path), "unchanged": True}
        if existing is not None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            history_root = RITU_ROOT / ".ritu" / "portal-history"
            backup = confined_path(history_root, f"{relative}.{timestamp}.bak")
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
            Path(temporary_name).replace(target)
        finally:
            if Path(temporary_name).exists():
                Path(temporary_name).unlink()
        digest = hashlib.sha256(payload).hexdigest()
        self.store.add_event(
            "portal_file_written",
            f"Portal file written: {str(relative).replace(chr(92), '/')}",
            {"scope": "portal", "path": str(relative).replace("\\", "/"), "sha256": digest, "summary": summary},
        )
        return {**self.read_text_file(scope, relative_path), "unchanged": False}

    def patch_scoped_text(
        self,
        scope: str,
        relative_path: str,
        find: str,
        replace: str,
        project: dict[str, Any] | None = None,
        summary: str = "",
    ) -> dict[str, Any]:
        if not find:
            raise ValueError("An exact find value is required.")
        current = self.read_text_file(scope, relative_path, project)
        occurrences = current["content"].count(find)
        if occurrences != 1:
            raise ValueError(f"Exact patch requires one match; found {occurrences}.")
        updated = current["content"].replace(find, replace, 1)
        return self.write_scoped_text(scope, relative_path, updated, project, summary)

    def file_context(
        self,
        project: dict[str, Any],
        max_characters: int = 48000,
    ) -> str:
        files = self.list_files("project", project, 200)
        chunks = ["Workspace file inventory:\n" + "\n".join(item["path"] for item in files)]
        remaining = max_characters - len(chunks[0])
        for item in files:
            if remaining <= 0 or not item["editable"] or item["size"] > remaining:
                continue
            try:
                record = self.read_text_file("project", item["path"], project)
            except ValueError:
                continue
            text = record["content"]
            chunks.append(f"### FILE: {item['path']}\n{text}")
            remaining -= len(text)
        return "\n\n".join(chunks)

    def portal_file_context(self, query: str, max_characters: int = 36000) -> str:
        files = self.list_files("portal", None, 300)
        inventory = "Portal source inventory:\n" + "\n".join(item["path"] for item in files)
        chunks = [inventory]
        remaining = max_characters - len(inventory)
        terms = {term.casefold() for term in query.replace("\\", " ").replace("/", " ").split() if len(term) >= 3}
        preferred = []
        for item in files:
            path_terms = set(item["path"].casefold().replace(".", " ").replace("-", " ").split())
            if terms & path_terms or item["path"] in {"index.html", "server.py", "powerhouse/config.py"}:
                preferred.append(item)
        for item in preferred:
            if remaining <= 0 or not item["editable"] or item["size"] > remaining:
                continue
            try:
                record = self.read_text_file("portal", item["path"])
            except ValueError:
                continue
            text = record["content"]
            chunks.append(f"### PORTAL FILE: {item['path']}\n{text}")
            remaining -= len(text)
        return "\n\n".join(chunks)

    def reference_context(self, project: dict[str, Any], max_characters: int = 24000) -> str:
        rows = self.store.all(
            "SELECT name,path,media_type FROM reference_files WHERE project_id=? ORDER BY created_at DESC LIMIT 20",
            (project["id"],),
        )
        chunks = []
        remaining = max_characters
        text_suffixes = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".py", ".html", ".css", ".js"}
        for row in rows:
            path = Path(row["path"])
            if path.suffix.lower() not in text_suffixes or not path.exists():
                chunks.append(f"[Stored reference: {row['name']} ({row['media_type']})]")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")[:remaining]
            chunks.append(f"### {row['name']}\n{text}")
            remaining -= len(text)
            if remaining <= 0:
                break
        return "\n\n".join(chunks)
