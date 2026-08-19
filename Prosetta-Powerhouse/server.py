from __future__ import annotations

import base64
import io
import json
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
from PIL import Image

from powerhouse import RituOrchestrator


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8080
MAX_BODY_BYTES = 25 * 1024 * 1024
MAX_IMAGE_EDGE = 2560

_engine: Any = None
_engine_lock = threading.Lock()
_ritu: RituOrchestrator | None = None
_ritu_lock = threading.Lock()


def get_engine() -> Any:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                from rapidocr import RapidOCR

                _engine = RapidOCR()
    return _engine


def get_ritu() -> RituOrchestrator:
    global _ritu
    if _ritu is None:
        with _ritu_lock:
            if _ritu is None:
                _ritu = RituOrchestrator()
    return _ritu


def normalize_result(result: Any) -> tuple[list[dict[str, Any]], float | None]:
    elapsed = None
    if isinstance(result, tuple) and len(result) == 2:
        result, elapsed = result

    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    boxes = getattr(result, "boxes", None)
    if texts is not None:
        rows = []
        for index, text in enumerate(texts):
            score = float(scores[index]) if scores is not None and index < len(scores) else None
            box = boxes[index].tolist() if boxes is not None and index < len(boxes) and hasattr(boxes[index], "tolist") else (boxes[index] if boxes is not None and index < len(boxes) else None)
            rows.append({"text": str(text), "score": score, "box": box})
        return rows, elapsed

    if isinstance(result, dict):
        texts = result.get("txts") or result.get("texts") or []
        scores = result.get("scores") or []
        boxes = result.get("boxes") or []
        return [
            {
                "text": str(text),
                "score": float(scores[index]) if index < len(scores) else None,
                "box": boxes[index] if index < len(boxes) else None,
            }
            for index, text in enumerate(texts)
        ], elapsed

    rows = []
    for item in result or []:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            box, text, score = item[0], item[1], item[2]
            rows.append({"text": str(text), "score": float(score), "box": box})
    return rows, elapsed


class RituHandler(SimpleHTTPRequestHandler):
    server_version = "RituLocal/1.0"

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request payload is empty or too large.")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            self.send_json(HTTPStatus.OK, get_ritu().health())
            return
        if path == "/api/company/status":
            self.send_json(HTTPStatus.OK, get_ritu().status())
            return
        if path == "/api/portal/state":
            self.send_json(HTTPStatus.OK, get_ritu().status())
            return
        if path == "/api/portal/files":
            try:
                result = get_ritu().list_files(
                    str((query.get("scope") or ["project"])[0]),
                    str((query.get("project") or [""])[0]) or None,
                )
                self.send_json(HTTPStatus.OK, result)
            except Exception as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})
            return
        if path == "/api/portal/file":
            try:
                result = get_ritu().read_file(
                    str((query.get("scope") or ["project"])[0]),
                    str((query.get("path") or [""])[0]),
                    str((query.get("project") or [""])[0]) or None,
                )
                self.send_json(HTTPStatus.OK, result)
            except Exception as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})
            return
        if path == "/api/training/status":
            self.send_json(HTTPStatus.OK, get_ritu().training_status())
            return
        if path == "/api/ocr/health":
            self.send_json(
                HTTPStatus.OK,
                {"ok": True, "engine": "RapidOCR", "loaded": _engine is not None, "local": True},
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            if self.path == "/api/state/screen":
                self.read_json()
                self.send_json(HTTPStatus.OK, {"ok": True})
                return

            if self.path == "/api/ritu/chat":
                payload = self.read_json()
                result = get_ritu().chat(
                    str(payload.get("message") or ""),
                    str(payload.get("session_id") or "default"),
                    payload.get("selected_context") if isinstance(payload.get("selected_context"), dict) else None,
                    str(payload.get("room") or "command"),
                )
                self.send_json(HTTPStatus.OK, result)
                return

            if self.path == "/api/company/upload":
                payload = self.read_json()
                result = get_ritu().upload_reference(
                    str(payload.get("filename") or "reference"),
                    str(payload.get("data") or ""),
                    str(payload.get("media_type") or "application/octet-stream"),
                    str(payload.get("project") or "") or None,
                )
                self.send_json(HTTPStatus.OK, result)
                return

            if self.path == "/api/company/run-task":
                payload = self.read_json()
                result = get_ritu().run_task(
                    str(payload.get("task_id") or ""),
                    sleep_after=bool(payload.get("sleep_after")),
                )
                self.send_json(HTTPStatus.OK, {"ok": True, "result": result, "company": get_ritu().status()})
                return

            if self.path == "/api/portal/task":
                payload = self.read_json()
                result = get_ritu().update_task_status(
                    str(payload.get("task") or payload.get("task_id") or ""),
                    str(payload.get("status") or ""),
                )
                self.send_json(HTTPStatus.OK, result)
                return

            if self.path == "/api/portal/file":
                payload = self.read_json()
                result = get_ritu().write_file(
                    str(payload.get("scope") or "project"),
                    str(payload.get("path") or ""),
                    str(payload.get("content") or ""),
                    str(payload.get("project") or "") or None,
                    str(payload.get("summary") or "Updated from localhost portal"),
                )
                self.send_json(HTTPStatus.OK, result)
                return

            if self.path == "/api/training/session":
                payload = self.read_json()
                result = get_ritu().train(
                    str(payload.get("topic") or ""),
                    str(payload.get("objective") or ""),
                    str(payload.get("category") or "Operations"),
                    str(payload.get("scope") or "global"),
                    str(payload.get("source_notes") or ""),
                )
                self.send_json(HTTPStatus.OK, result)
                return

            if self.path != "/api/ocr":
                self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
                return

            payload = self.read_json()
            image_data = payload.get("image", "")
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            raw = base64.b64decode(image_data, validate=True)
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            if max(image.size) > MAX_IMAGE_EDGE:
                image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)

            started = time.perf_counter()
            result = get_engine()(np.asarray(image))
            rows, engine_elapsed = normalize_result(result)
            rows = [row for row in rows if row["text"].strip()]
            text = "\n".join(row["text"].strip() for row in rows)
            scores = [row["score"] for row in rows if row["score"] is not None]
            confidence = sum(scores) / len(scores) if scores else None

            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "text": text,
                    "lines": rows,
                    "line_count": len(rows),
                    "confidence": confidence,
                    "duration_ms": round((time.perf_counter() - started) * 1000),
                    "engine_duration": engine_elapsed if isinstance(engine_elapsed, (int, float, str)) else None,
                    "image": {"width": image.width, "height": image.height},
                    "local": True,
                },
            )
        except Exception as error:
            self.send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": str(error) or error.__class__.__name__},
            )


def main() -> None:
    print(f"Ritu Command Center: http://{HOST}:{PORT}")
    print("RapidOCR: local-only screen reading enabled")
    ThreadingHTTPServer((HOST, PORT), lambda *args, **kwargs: RituHandler(*args, directory=str(ROOT), **kwargs)).serve_forever()


if __name__ == "__main__":
    main()
