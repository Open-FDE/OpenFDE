"""Optional LLM client for ELICIT and INDUCE.

Design choice, stated plainly because it is a real question for enterprise
deployments: **the Apprentice Loop does not require an LLM to run.** OBSERVE,
the baseline elicitation interview, deterministic induction, ACT compilation
and heuristic attribution all work offline. An LLM, when configured, *raises
the ceiling* of ELICIT (better probe wording) and INDUCE (better structuring
of free-text answers) — it is not a hard dependency.

This keeps two enterprise realities honest:
  1. Some customers cannot send on-site data to an external model. The loop
     must still produce Judgment Units locally.
  2. "Do we have to call a big model to extract this?" — No. The model is a
     quality lever, not the mechanism.

Configuration (any OpenAI-compatible endpoint):
    OPENFDE_LLM_BASE_URL   e.g. https://api.openai.com/v1  (or a gateway)
    OPENFDE_LLM_API_KEY    the key
    OPENFDE_LLM_MODEL      e.g. gpt-4o-mini / gemini-3-flash / qwen2.5 ...

Secrets are only ever read from the environment — never stored in the repo,
a Judgment Unit, or a connector spec.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional


class LLMConfig:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = base_url or os.environ.get("OPENFDE_LLM_BASE_URL")
        self.api_key = api_key or os.environ.get("OPENFDE_LLM_API_KEY")
        self.model = model or os.environ.get("OPENFDE_LLM_MODEL", "gpt-4o-mini")

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)


class LLMClient:
    """Minimal OpenAI-compatible chat client. Never raises on missing config —
    callers check `.enabled` and fall back to deterministic behavior.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def chat(self, messages: List[dict], temperature: float = 0.2, max_tokens: int = 1024) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            import httpx  # optional dependency (extras: openfde[llm])
        except ImportError:
            return None
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            # The loop must survive a flaky/unreachable model. Fall back silently.
            return None

    def json(self, messages: List[dict], temperature: float = 0.0) -> Optional[dict]:
        """Chat and parse a JSON object from the reply, tolerating fenced blocks."""
        text = self.chat(messages, temperature=temperature)
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if 0 <= start < end:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None


__all__ = ["LLMClient", "LLMConfig"]
