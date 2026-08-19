from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def request(self, path: str, payload: dict[str, Any] | None = None, timeout: int = 180) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"} if body else {},
            method="POST" if body else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"Ollama is unavailable: {error}") from error

    def health(self) -> dict[str, Any]:
        version = self.request("/api/version", timeout=5)
        tags = self.request("/api/tags", timeout=10)
        models = [item.get("name") for item in tags.get("models", [])]
        return {"online": True, "version": version.get("version"), "models": models, "model": self.model}

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.2,
        timeout: int = 240,
        max_tokens: int = 768,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "30m",
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        result = self.request("/api/chat", payload, timeout=timeout)
        content = result.get("message", {}).get("content", "")
        if not content.strip():
            raise RuntimeError("Ollama returned an empty response.")
        return content.strip()
