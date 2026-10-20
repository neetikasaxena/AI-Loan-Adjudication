"""Minimal client for an OpenAI-compatible chat-completions endpoint (e.g. an internal LLM gateway)."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv

class LLMError(RuntimeError):
    pass

def parse_json_object(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise LLMError(f"No JSON object in LLM output: {text[:200]!r}")
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"Invalid JSON from LLM: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMError("LLM output is not a JSON object")
    return data

@dataclass
class LLMClient:
    base_url: str
    model: str
    api_key: str | None = None
    api_key_header: str = "Authorization"
    extra_headers: dict[str, str] = field(default_factory=dict)
    verify: str | bool = True
    timeout: float = 60.0
    max_retries: int = 3
    json_mode: bool = True

    @classmethod
    def from_env(cls) -> "LLMClient | None":
        """Build from LLM_* environment variables (and .env). Returns None when no endpoint is configured."""
        load_dotenv()
        base_url = os.getenv("LLM_BASE_URL", "").strip()
        if not base_url:
            return None
        model = os.getenv("LLM_MODEL", "").strip()
        if not model:
            raise LLMError("LLM_MODEL must be set when LLM_BASE_URL is set")
        try:
            extra_headers = json.loads(os.getenv("LLM_EXTRA_HEADERS") or "{}")
        except json.JSONDecodeError as exc:
            raise LLMError("LLM_EXTRA_HEADERS must be a JSON object") from exc
        return cls(
            base_url=base_url.rstrip("/"),
            model=model,
            api_key=os.getenv("LLM_API_KEY") or None,
            api_key_header=os.getenv("LLM_API_KEY_HEADER", "Authorization"),
            extra_headers=extra_headers,
            verify=os.getenv("LLM_CA_BUNDLE") or True,
            timeout=float(os.getenv("LLM_TIMEOUT", "60")),
            json_mode=os.getenv("LLM_JSON_MODE", "true").lower() == "true",
        )

    @property
    def url(self) -> str:
        return self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            is_bearer = self.api_key_header.lower() == "authorization"
            headers[self.api_key_header] = f"Bearer {self.api_key}" if is_bearer else self.api_key
        return headers

    def chat(self, messages: list[dict], temperature: float = 0.0, max_tokens: int = 800) -> str:
        body: dict = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(self.url, headers=self._headers(), json=body, timeout=self.timeout, verify=self.verify)
            except requests.RequestException as exc:
                last_error = exc
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()["choices"][0]["message"]["content"]
                    except (KeyError, IndexError, TypeError, ValueError) as exc:
                        raise LLMError(f"Unexpected response shape: {resp.text[:300]}") from exc
                if resp.status_code not in (408, 429) and resp.status_code < 500:
                    raise LLMError(f"HTTP {resp.status_code}: {resp.text[:300]}")
                last_error = LLMError(f"HTTP {resp.status_code}")
            if attempt < self.max_retries:
                time.sleep(2**attempt)
        raise LLMError(f"LLM call failed after {self.max_retries + 1} attempts: {last_error}")

    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        return parse_json_object(self.chat(messages, **kwargs))
