from pathlib import Path
import unittest

import main


ROOT = Path(__file__).resolve().parents[1]


class SingleFileStructureTest(unittest.TestCase):
    def test_flask_db_helpers_are_defined_in_main(self):
        self.assertTrue(callable(main.fetch_all))
        self.assertTrue(callable(main.execute))
        self.assertTrue(callable(main.execute_many))
        self.assertIsInstance(main.TCP_HOST, str)
        self.assertIsInstance(main.TCP_PORT, int)

    def test_separate_config_and_db_modules_are_removed(self):
        self.assertFalse((ROOT / "config.py").exists())
        self.assertFalse((ROOT / "db.py").exists())


if __name__ == "__main__":
    unittest.main()
