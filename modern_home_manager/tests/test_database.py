import tempfile
import unittest
from pathlib import Path

from modern_home_manager.database import (
    build_dashboard_payload,
    initialize_database,
    record_device_frame,
    room_payload,
    set_actuator_active,
)


class ModernHomeDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "home.db"
        initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dashboard_payload_uses_seeded_database(self):
        payload = build_dashboard_payload(self.db_path)

        self.assertEqual([room["id"] for room in payload["rooms"]], ["living", "bedroom", "kitchen"])
        self.assertEqual(payload["status"]["gateway"], "127.0.0.1")
        self.assertGreaterEqual(len(payload["sensors"]), 5)
        self.assertGreaterEqual(len(payload["actuators"]), 6)

    def test_room_payload_filters_sensors_and_actuators(self):
        payload = room_payload(self.db_path, "bedroom")

        self.assertEqual(payload["room"]["id"], "bedroom")
        self.assertTrue(all(item["room"] == "bedroom" for item in payload["sensors"]))
        self.assertTrue(all(item["room"] == "bedroom" for item in payload["actuators"]))

    def test_set_actuator_active_persists_latest_state(self):
        actuator = set_actuator_active(self.db_path, "kitchen-plug", True)
        payload = build_dashboard_payload(self.db_path)
        kitchen_plug = next(item for item in payload["actuators"] if item["id"] == "kitchen-plug")

        self.assertTrue(actuator["active"])
        self.assertTrue(kitchen_plug["active"])
        self.assertEqual(kitchen_plug["detail"], "켜짐")

    def test_record_device_frame_updates_sensor_and_actuator_logs(self):
        record_device_frame(
            self.db_path,
            {
                "device_id": "pico_living_room",
                "sensors": {"temperature": 28.4, "humidity": 58, "light": 444},
                "actuators": {"living-light": False},
            },
        )
        payload = build_dashboard_payload(self.db_path)
        living = next(room for room in payload["rooms"] if room["id"] == "living")
        living_light = next(item for item in payload["actuators"] if item["id"] == "living-light")

        self.assertEqual(living["temperature"], 28.4)
        self.assertEqual(living["humidity"], 58)
        self.assertEqual(living["light"], 444)
        self.assertFalse(living_light["active"])


if __name__ == "__main__":
    unittest.main()
