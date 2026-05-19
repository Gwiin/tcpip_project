import tempfile
import unittest
from pathlib import Path

from modern_home_manager.app import create_app


class ModernHomeAppTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "home.db"
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dashboard_api_returns_database_payload(self):
        response = self.client.get("/api/dashboard")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["rooms"][0]["id"], "living")
        self.assertIn("status", payload)

    def test_dashboard_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("스마트홈 대시보드".encode("utf-8"), response.data)

    def test_toggle_actuator_updates_database_payload(self):
        response = self.client.post("/api/actuators/kitchen-plug/toggle", json={"active": True})
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["active"])

    def test_unknown_room_returns_404(self):
        response = self.client.get("/api/rooms/garage")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
