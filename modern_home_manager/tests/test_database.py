import unittest

from modern_home_manager import database


class ModernHomeDatabaseMappingTest(unittest.TestCase):
    def test_room_slug_and_int_id_round_trip(self):
        self.assertEqual(database.room_slug(1), "living")
        self.assertEqual(database.room_int_id("living"), 1)
        self.assertEqual(database.room_int_id("room-7"), 7)
        self.assertIsNone(database.room_int_id("garage"))

    def test_actuator_api_id_and_int_id_round_trip(self):
        self.assertEqual(database.actuator_api_id(3), "actuator-3")
        self.assertEqual(database.actuator_int_id("actuator-3"), 3)
        self.assertEqual(database.actuator_int_id("3"), 3)
        self.assertIsNone(database.actuator_int_id("living-light"))

    def test_format_sensor_value(self):
        self.assertEqual(database.format_sensor_value("temperature", 23.456, "C"), "23.5C")
        self.assertEqual(database.format_sensor_value("humidity", 45.2, "%"), "45 %")
        self.assertEqual(database.format_sensor_value("motion", 1, "bool"), "감지")
        self.assertEqual(database.format_sensor_value("motion", 0, "bool"), "없음")


if __name__ == "__main__":
    unittest.main()
