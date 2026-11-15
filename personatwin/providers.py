"""OpenAI-compatible chat-completions client; configure any compatible provider by URL/model/key."""
from __future__ import annotations
import os, httpx

class ProviderError(RuntimeError): pass

class ChatProvider:
    def __init__(self, name: str, base_url: str, model: str, api_key: str | None = None, timeout: float = 60):
        self.name, self.base_url, self.model = name, base_url.rstrip("/"), model
        self.api_key, self.timeout = api_key or "", timeout
    @classmethod
    def from_env(cls, prefix: str):
        return cls(prefix.lower(), os.getenv(f"{prefix}_BASE_URL", "https://api.openai.com/v1"),
                   os.getenv(f"{prefix}_MODEL", ""), os.getenv(f"{prefix}_API_KEY", ""),
                   float(os.getenv("LLM_TIMEOUT", "60")))
    def complete(self, messages, temperature=0.2, json_mode=False):
        if not self.model: raise ProviderError(f"No model configured for provider {self.name}.")
        if not self.api_key: raise ProviderError(f"No API key configured for provider {self.name}.")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": messages, "temperature": temperature}
        if json_mode: body["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
                response.raise_for_status(); data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc: raise ProviderError(f"Provider {self.name} request failed: {exc}") from exc

class ProviderRegistry:
    def __init__(self):
        self.providers = {"LLM_A": ChatProvider.from_env("LLM_A"), "LLM_B": ChatProvider.from_env("LLM_B"), "JUDGE": ChatProvider.from_env("JUDGE")}
    def get(self, name):
        try: return self.providers[name]
        except KeyError: raise ProviderError(f"Unknown provider {name}; use LLM_A, LLM_B, or JUDGE.")
