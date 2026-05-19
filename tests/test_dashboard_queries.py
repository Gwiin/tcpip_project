import unittest

import main


class DashboardQueriesTest(unittest.TestCase):
    def test_unknown_user_location_uses_readable_korean_text(self):
        self.assertIn("\\uc704\\uce58 \\uc5c6\\uc74c", ascii(main.USER_LOCATION_SQL))


if __name__ == "__main__":
    unittest.main()
