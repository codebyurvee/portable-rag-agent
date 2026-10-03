"""Minimal Qwen3-8B adapter via an OpenAI-compatible endpoint (env-configured)."""

import os


class QwenModel:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv("QWEN_BASE_URL")
        self.model = model or os.getenv("QWEN_MODEL", "qwen/qwen3-8b")
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def generate(self, messages: list[dict], temperature: float = 0.2) -> str:
        if not self.configured:
            raise RuntimeError("Qwen model not configured (set QWEN_API_KEY and QWEN_BASE_URL)")
        resp = self._get_client().chat.completions.create(
            model=self.model, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""
