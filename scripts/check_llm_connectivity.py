#!/usr/bin/env python
"""
Quick connectivity check for configured LLM providers.
- Runs minimal model-list calls for providers with configured API keys.
- Exits 0 if all configured providers respond, 1 otherwise.
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

from fastapi import HTTPException

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.llm_router import llm_router
from backend.app.schemas import LLMProvider


async def check_provider(provider: LLMProvider, env_var: str) -> Tuple[bool, str]:
    try:
        models = await llm_router.list_models(provider)
        sample = ", ".join(m.id for m in models[:3]) if models else "no models returned"
        return True, f"[ok] {provider.value}: {len(models)} models (sample: {sample})"
    except HTTPException as exc:
        return False, f"[fail] {provider.value}: {exc.detail}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"[fail] {provider.value}: {exc}"


async def main() -> int:
    providers: List[Tuple[LLMProvider, str]] = []
    if settings.openai_api_key:
        providers.append((LLMProvider.openai, "OPENAI_API_KEY"))
    if settings.anthropic_api_key:
        providers.append((LLMProvider.anthropic, "ANTHROPIC_API_KEY"))
    if settings.gemini_api_key:
        providers.append((LLMProvider.gemini, "GEMINI_API_KEY"))

    if not providers:
        print("No provider API keys configured; skipping LLM connectivity check.")
        return 0

    failures = False
    for provider, env_var in providers:
        ok, message = await check_provider(provider, env_var)
        print(message)
        failures = failures or not ok

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
