import unittest
from unittest.mock import patch

from modern_home_manager.app import create_app


DASHBOARD_PAYLOAD = {
    "status": {
        "connection": "MySQL 연결됨",
        "security": "해제",
        "averageTemperature": "23.0C",
        "averageHumidity": "45%",
        "currentTime": "2026-05-20 12:00:00",
        "gateway": "127.0.0.1:3306",
        "firmware": "modern-mysql-v1",
    },
    "rooms": [{"id": "living", "name": "거실", "temperature": 23.0, "humidity": 45, "light": 300, "devices_on": 1, "spark": [22, 23], "image": "images/living-room-photo.png", "status": "사용중", "color": "teal"}],
    "sensors": [],
    "temperatures": [],
    "actuators": [{"id": "actuator-1", "room": "living", "icon": "light", "name": "거실 조명", "detail": "OFF", "active": False}],
    "reservations": [],
    "location": {"user": "관리자", "time": "-", "updated": "-", "source": "mysql", "accuracy": None, "note": ""},
    "logs": [],
}


class ModernHomeAppTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def login_session(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["user_name"] = "관리자"
            session["role"] = "ADMIN"

    @patch("modern_home_manager.app.build_dashboard_payload", return_value=DASHBOARD_PAYLOAD)
    def test_dashboard_api_returns_mysql_payload(self, _mock_payload):
        response = self.client.get("/api/dashboard")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"]["connection"], "MySQL 연결됨")
        self.assertEqual(payload["rooms"][0]["id"], "living")

    def test_dashboard_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("스마트홈 대시보드".encode("utf-8"), response.data)

    @patch("modern_home_manager.app.build_dashboard_payload", return_value=DASHBOARD_PAYLOAD)
    @patch("modern_home_manager.app.set_actuator_active", return_value={**DASHBOARD_PAYLOAD["actuators"][0], "active": True})
    def test_toggle_actuator_updates_mysql_payload(self, _mock_toggle, _mock_payload):
        self.login_session()
        response = self.client.post("/api/actuators/actuator-1/toggle", json={"active": True})
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["active"])

    @patch("modern_home_manager.app.build_dashboard_payload", return_value=DASHBOARD_PAYLOAD)
    def test_toggle_requires_login(self, _mock_payload):
        response = self.client.post("/api/actuators/actuator-1/toggle", json={"active": True})
        payload = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(payload["success"])

    @patch("modern_home_manager.app.authenticate_user", return_value={"user_id": 1, "user_name": "관리자", "role": "ADMIN"})
    def test_login_uses_sql_user_table_flow(self, mock_authenticate):
        response = self.client.post("/api/session/login", json={"username": "관리자", "password": "admin123"})
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["loggedIn"])
        self.assertEqual(payload["user"], "관리자")
        mock_authenticate.assert_called_once_with("관리자", "admin123")

    @patch("modern_home_manager.app.create_user_account", return_value={"user_id": 4, "user_name": "새사용자", "role": "GUEST"})
    def test_register_creates_sql_user_account(self, mock_create):
        response = self.client.post("/api/session/register", json={"username": "새사용자", "password": "new-pass"})
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(payload["loggedIn"])
        self.assertEqual(payload["user"], "새사용자")
        mock_create.assert_called_once_with("새사용자", "new-pass")

    def test_logout_clears_session(self):
        self.login_session()
        response = self.client.post("/api/session/logout")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(payload["loggedIn"])

    @patch("modern_home_manager.app.record_device_frame")
    def test_pico_ingest_accepts_frame(self, mock_record):
        response = self.client.post(
            "/api/pico/ingest",
            json={"device_id": "pico_living_room", "sensors": {"temperature": 24.1}},
        )

        self.assertEqual(response.status_code, 200)
        mock_record.assert_called_once()

    @patch("modern_home_manager.app.room_payload", return_value=None)
    def test_unknown_room_returns_404(self, _mock_room):
        response = self.client.get("/api/rooms/garage")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
