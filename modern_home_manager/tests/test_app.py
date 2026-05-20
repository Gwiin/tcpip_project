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
        self.client = self.app.test_client()

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
        response = self.client.post("/api/actuators/actuator-1/toggle", json={"active": True})
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["active"])

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
