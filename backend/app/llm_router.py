from __future__ import annotations

from typing import List, Optional

import httpx
from fastapi import HTTPException, status

from .config import settings
from .schemas import (
    LLMChatRequest,
    LLMCompletionRequest,
    LLMModelOut,
    LLMProvider,
    LLMMessage,
)


class LLMRouter:
    def __init__(self):
        self._anthropic_version = "2023-06-01"
        self._openai_version_path = "/v1"
        self._anthropic_version_path = "/v1"
        self._gemini_version_path = "/v1beta"

    def _require_key(self, key: Optional[str], provider: LLMProvider) -> str:
        if not key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider.value.capitalize()} API key is not configured",
            )
        return key

    async def list_models(self, provider: LLMProvider) -> List[LLMModelOut]:
        if provider == LLMProvider.openai:
            key = self._require_key(settings.openai_api_key, provider)
            url = f"{self._openai_base()}/models"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers={"Authorization": f"Bearer {key}"})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("OpenAI", resp))
            data = resp.json().get("data", [])
            return [LLMModelOut(id=m.get("id", ""), provider=provider, description=m.get("owned_by")) for m in data]

        if provider == LLMProvider.anthropic:
            key = self._require_key(settings.anthropic_api_key, provider)
            url = f"{self._anthropic_base()}/models"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    headers={
                        "x-api-key": key,
                        "anthropic-version": self._anthropic_version,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Anthropic", resp))
            data = resp.json().get("data", [])
            return [LLMModelOut(id=m.get("id", ""), provider=provider, description=m.get("display_name")) for m in data]

        if provider == LLMProvider.gemini:
            key = self._require_key(settings.gemini_api_key, provider)
            url = f"{self._gemini_base()}/models?key={key}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Gemini", resp))
            models = resp.json().get("models", [])
            return [
                LLMModelOut(
                    id=m.get("name", ""),
                    provider=provider,
                    description=m.get("description"),
                )
                for m in models
            ]

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    async def completion(self, payload: LLMCompletionRequest) -> str:
        if payload.provider == LLMProvider.openai:
            key = self._require_key(settings.openai_api_key, payload.provider)
            url = f"{self._openai_base()}/completions"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": payload.model,
                        "prompt": payload.prompt,
                        "max_tokens": payload.max_tokens,
                        "temperature": payload.temperature,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("OpenAI completion", resp))
            return resp.json().get("choices", [{}])[0].get("text", "")

        if payload.provider == LLMProvider.anthropic:
            key = self._require_key(settings.anthropic_api_key, payload.provider)
            url = f"{self._anthropic_base()}/messages"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={
                        "x-api-key": key,
                        "anthropic-version": self._anthropic_version,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": payload.model,
                        "max_tokens": payload.max_tokens or 256,
                        "messages": [{"role": "user", "content": payload.prompt}],
                        "temperature": payload.temperature,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Anthropic completion", resp))
            return self._extract_anthropic_text(resp.json())

        if payload.provider == LLMProvider.gemini:
            key = self._require_key(settings.gemini_api_key, payload.provider)
            url = f"{self._gemini_base()}/models/{payload.model}:generateContent?key={key}"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"role": "user", "parts": [{"text": payload.prompt}]}],
                        "generationConfig": {
                            "temperature": payload.temperature,
                            "maxOutputTokens": payload.max_tokens,
                        },
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Gemini completion", resp))
            return self._extract_gemini_text(resp.json())

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    async def chat(self, payload: LLMChatRequest) -> str:
        if payload.provider == LLMProvider.openai:
            key = self._require_key(settings.openai_api_key, payload.provider)
            url = f"{self._openai_base()}/chat/completions"
            messages = self._build_openai_messages(payload.messages, payload.system_prompt)
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": payload.model,
                        "messages": messages,
                        "temperature": payload.temperature,
                        "max_tokens": payload.max_tokens,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("OpenAI chat", resp))
            return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        if payload.provider == LLMProvider.anthropic:
            key = self._require_key(settings.anthropic_api_key, payload.provider)
            url = f"{self._anthropic_base()}/messages"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={
                        "x-api-key": key,
                        "anthropic-version": self._anthropic_version,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": payload.model,
                        "max_tokens": payload.max_tokens or 512,
                        "messages": self._build_anthropic_messages(payload.messages),
                        "system": payload.system_prompt,
                        "temperature": payload.temperature,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Anthropic chat", resp))
            return self._extract_anthropic_text(resp.json())

        if payload.provider == LLMProvider.gemini:
            key = self._require_key(settings.gemini_api_key, payload.provider)
            url = f"{self._gemini_base()}/models/{payload.model}:generateContent?key={key}"
            contents = self._build_gemini_messages(payload.messages, payload.system_prompt)
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": contents,
                        "generationConfig": {
                            "temperature": payload.temperature,
                            "maxOutputTokens": payload.max_tokens,
                        },
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=self._error_detail("Gemini chat", resp))
            return self._extract_gemini_text(resp.json())

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    def _build_openai_messages(self, messages: List[LLMMessage], system_prompt: Optional[str]) -> List[dict]:
        base_messages: List[dict] = []
        if system_prompt:
            base_messages.append({"role": "system", "content": system_prompt})
        base_messages.extend([{"role": m.role, "content": m.content} for m in messages])
        return base_messages

    def _build_anthropic_messages(self, messages: List[LLMMessage]) -> List[dict]:
        return [{"role": "user" if m.role == "system" else m.role, "content": m.content} for m in messages if m.content]

    def _build_gemini_messages(self, messages: List[LLMMessage], system_prompt: Optional[str]) -> List[dict]:
        contents: List[dict] = []
        if system_prompt:
            contents.append({"role": "system", "parts": [{"text": system_prompt}]})
        for message in messages:
            contents.append({"role": message.role, "parts": [{"text": message.content}]})
        return contents

    def _extract_anthropic_text(self, data: dict) -> str:
        content = data.get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return "\n".join([t for t in text_parts if t])

    def _extract_gemini_text(self, data: dict) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        return "".join([p.get("text", "") for p in parts if p.get("text")])

    def _openai_base(self) -> str:
        base = settings.openai_base_url.rstrip("/")
        if base.endswith(self._openai_version_path):
            return base
        return f"{base}{self._openai_version_path}"

    def _anthropic_base(self) -> str:
        base = settings.anthropic_base_url.rstrip("/")
        if base.endswith(self._anthropic_version_path):
            return base
        return f"{base}{self._anthropic_version_path}"

    def _gemini_base(self) -> str:
        base = settings.gemini_base_url.rstrip("/")
        if base.endswith(self._gemini_version_path):
            return base
        return f"{base}{self._gemini_version_path}"

    def _error_detail(self, label: str, resp: httpx.Response) -> str:
        try:
            data = resp.json()
            message = data.get("error", {}).get("message") or data.get("message")
            if message:
                return f"{label} error: {message}"
        except Exception:
            pass
        return f"{label} failed with status {resp.status_code}: {resp.text}"


llm_router = LLMRouter()
