import unittest
from typing import Any

from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.llm_router import llm_router
from backend.app.main import app
from backend.app.schemas import LLMProvider
from backend.app.deps import require_admin


class DummyAdmin:
    def __init__(self) -> None:
        self.id = "admin"
        self.role = "admin"
        self.email = "admin@example.com"


class LLMRouterConnectivityTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_models(self):
        if not settings.openai_api_key:
            self.skipTest("OPENAI_API_KEY not set")
        models = await llm_router.list_models(LLMProvider.openai)
        self.assertGreater(len(models), 0)

    async def test_anthropic_models(self):
        if not settings.anthropic_api_key:
            self.skipTest("ANTHROPIC_API_KEY not set")
        models = await llm_router.list_models(LLMProvider.anthropic)
        self.assertGreater(len(models), 0)

    async def test_gemini_models(self):
        if not settings.gemini_api_key:
            self.skipTest("GEMINI_API_KEY not set")
        models = await llm_router.list_models(LLMProvider.gemini)
        self.assertGreater(len(models), 0)


class BackendEndpointConnectivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[require_admin] = lambda: DummyAdmin()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(require_admin, None)

    def test_openai_models_endpoint(self):
        if not settings.openai_api_key:
            self.skipTest("OPENAI_API_KEY not set")
        response = self.client.get("/llm/models", params={"provider": "openai"})
        self.assertEqual(response.status_code, 200, msg=response.text)
        data: list[Any] = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_anthropic_models_endpoint(self):
        if not settings.anthropic_api_key:
            self.skipTest("ANTHROPIC_API_KEY not set")
        response = self.client.get("/llm/models", params={"provider": "anthropic"})
        self.assertEqual(response.status_code, 200, msg=response.text)
        data: list[Any] = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_gemini_models_endpoint(self):
        if not settings.gemini_api_key:
            self.skipTest("GEMINI_API_KEY not set")
        response = self.client.get("/llm/models", params={"provider": "gemini"})
        self.assertEqual(response.status_code, 200, msg=response.text)
        data: list[Any] = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
