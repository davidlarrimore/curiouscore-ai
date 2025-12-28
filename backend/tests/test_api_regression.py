import os
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).with_name("test_app.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

from backend.app.auth import decode_token
from backend.app.config import settings
from backend.app.main import app


def auth_header(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@contextmanager
def override_settings(**kwargs: Any):
    original: Dict[str, Any] = {}
    for key, value in kwargs.items():
        original[key] = getattr(settings, key)
        setattr(settings, key, value)
    try:
        yield
    finally:
        for key, value in original.items():
            setattr(settings, key, value)


class APITestCase(unittest.TestCase):
    def setUp(self):
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
        self.client_ctx = TestClient(app)
        self.client = self.client_ctx.__enter__()

    def tearDown(self):
        self.client_ctx.__exit__(None, None, None)
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def register_user(self, email: str = "admin@example.com", password: str = "password123") -> str:
        response = self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "username": email.split("@")[0]},
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        data = response.json()
        self.assertIn("access_token", data)
        return data["access_token"]

    def fetch_challenges(self) -> List[Dict[str, Any]]:
        response = self.client.get("/challenges")
        self.assertEqual(response.status_code, 200, msg=response.text)
        return response.json()

    def test_register_and_login_flow(self):
        token = self.register_user()
        login_resp = self.client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
        )
        self.assertEqual(login_resp.status_code, 200, msg=login_resp.text)
        me_resp = self.client.get("/auth/me", headers=auth_header(token))
        self.assertEqual(me_resp.status_code, 200, msg=me_resp.text)
        payload = decode_token(token)
        self.assertEqual(payload.get("sub"), me_resp.json().get("id"))

    def test_duplicate_email_rejected(self):
        self.register_user()
        dup_resp = self.client.post(
            "/auth/register",
            json={"email": "admin@example.com", "password": "newpass", "username": "admin2"},
        )
        self.assertEqual(dup_resp.status_code, 400)
        self.assertIn("Email already registered", dup_resp.text)

    def test_profile_update_persists(self):
        token = self.register_user()
        update = {
            "username": "updated-name",
            "avatar_url": "https://example.com/avatar.png",
            "xp": 250,
            "level": 3,
        }
        resp = self.client.patch("/profile", headers=auth_header(token), json=update)
        self.assertEqual(resp.status_code, 200, msg=resp.text)
        body = resp.json()
        self.assertEqual(body["username"], update["username"])
        self.assertEqual(body["avatar_url"], update["avatar_url"])
        self.assertEqual(body["xp"], update["xp"])
        self.assertEqual(body["level"], update["level"])

    def test_admin_guard_blocks_non_admin_user(self):
        admin_token = self.register_user(email="admin@example.com")
        user_token = self.register_user(email="user@example.com", password="password321")
        admin_resp = self.client.get("/admin/challenges", headers=auth_header(admin_token))
        self.assertEqual(admin_resp.status_code, 200, msg=admin_resp.text)
        user_resp = self.client.get("/admin/challenges", headers=auth_header(user_token))
        self.assertEqual(user_resp.status_code, 403)

    def test_challenge_activation_filters_public_listing(self):
        token = self.register_user()
        challenges = self.fetch_challenges()
        self.assertGreaterEqual(len(challenges), 1)
        target_id = challenges[0]["id"]
        deactivate = self.client.patch(
            f"/admin/challenges/{target_id}/activation",
            headers=auth_header(token),
            json={"is_active": False},
        )
        self.assertEqual(deactivate.status_code, 200, msg=deactivate.text)
        public = self.fetch_challenges()
        self.assertTrue(all(chal["id"] != target_id for chal in public))

    def test_progress_update_persists_messages_and_scores(self):
        token = self.register_user()
        challenge_id = self.fetch_challenges()[0]["id"]
        start_resp = self.client.post(f"/progress/{challenge_id}/start", headers=auth_header(token))
        self.assertEqual(start_resp.status_code, 200, msg=start_resp.text)
        message = {
            "role": "assistant",
            "content": "Keep going!",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "questionType": "multiple_choice",
                "options": ["a", "b", "c"],
                "correctAnswer": 1,
                "phase": 1,
                "progressIncrement": 15,
                "scoreChange": 10,
                "hint": "Remember the basics",
                "isComplete": False,
            },
        }
        update_payload = {
            "progress_percent": 20,
            "score": 10,
            "status": "in_progress",
            "messages": [message],
            "current_phase": 2,
            "mistakes_count": 1,
        }
        update_resp = self.client.patch(
            f"/progress/{challenge_id}",
            headers=auth_header(token),
            json=update_payload,
        )
        self.assertEqual(update_resp.status_code, 200, msg=update_resp.text)
        progress = update_resp.json()
        self.assertEqual(progress["progress_percent"], 20)
        self.assertEqual(progress["score"], 10)
        self.assertEqual(progress["status"], "in_progress")
        self.assertEqual(progress["current_phase"], 2)
        self.assertEqual(progress["mistakes_count"], 1)
        self.assertEqual(len(progress["messages"]), 1)
        self.assertEqual(progress["messages"][0]["metadata"]["progressIncrement"], 15)

    def test_progress_reset_sets_defaults(self):
        token = self.register_user()
        challenge_id = self.fetch_challenges()[0]["id"]
        self.client.post(f"/progress/{challenge_id}/start", headers=auth_header(token))
        self.client.patch(
            f"/progress/{challenge_id}",
            headers=auth_header(token),
            json={"progress_percent": 50, "score": 25, "status": "in_progress"},
        )
        reset_resp = self.client.post(f"/progress/{challenge_id}/reset", headers=auth_header(token))
        self.assertEqual(reset_resp.status_code, 200, msg=reset_resp.text)
        body = reset_resp.json()
        self.assertEqual(body["progress_percent"], 0)
        self.assertEqual(body["score"], 0)
        self.assertEqual(body["status"], "not_started")
        self.assertEqual(body["current_phase"], 1)
        self.assertEqual(body["mistakes_count"], 0)
        self.assertEqual(body["messages"], [])

    def test_chat_requires_configured_model(self):
        token = self.register_user()
        challenge = self.fetch_challenges()[0]
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            "systemPrompt": challenge["system_prompt"],
            "challengeTitle": challenge["title"],
            "challengeId": challenge["id"],
            "currentPhase": 1,
        }
        with override_settings(default_llm_provider=None, default_llm_model=None):
            chat_resp = self.client.post("/chat", headers=auth_header(token), json=payload)
        self.assertEqual(chat_resp.status_code, 400, msg=chat_resp.text)
        self.assertIn("No model configured", chat_resp.text)


if __name__ == "__main__":
    unittest.main()
