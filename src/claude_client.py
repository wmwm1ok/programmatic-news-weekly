"""
Claude API client for summary and translation tasks.
"""

from __future__ import annotations

from typing import Any, Optional

import json
import requests

from config.settings import CLAUDE_API_KEY, CLAUDE_ENDPOINT, CLAUDE_HOST, CLAUDE_MODEL


class ClaudeClient:
    """Thin wrapper around the configured Claude gateway endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or CLAUDE_API_KEY
        self.endpoint = endpoint or CLAUDE_ENDPOINT
        self.host = CLAUDE_HOST
        self.model = model or CLAUDE_MODEL

        if not self.api_key:
            raise ValueError("Claude API Key 未设置，请设置 CLAUDE_API_KEY 环境变量")

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 300,
        temperature: float = 0.3,
        system: Optional[str] = None,
        timeout: int = 60,
    ) -> Optional[str]:
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Host": self.host,
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
            "top_p": 1,
            "top_k": 250,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            data["system"] = system

        response = requests.post(
            self.endpoint,
            headers=headers,
            data=json.dumps(data),
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()
        return self._extract_text(result)

    def _extract_text(self, result: Any) -> Optional[str]:
        if not result:
            return None

        if isinstance(result, dict):
            choices = result.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

            content = result.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if text:
                            parts.append(text)
                    elif isinstance(item, str):
                        parts.append(item)
                text = "".join(parts).strip()
                if text:
                    return text

            message = result.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

            for key in ("text", "answer", "output"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            data = result.get("data")
            if data is not None:
                return self._extract_text(data)

        return None
