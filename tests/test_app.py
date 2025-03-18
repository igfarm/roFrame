import unittest
from app import is_screen_on


class TestIsScreenOn(unittest.TestCase):
    def test_normal_range_screen_on(self):
        # Screen should be on between on_hour and off_hour
        self.assertTrue(is_screen_on(10, 9, 17))  # Current hour is within range
        self.assertTrue(is_screen_on(16, 9, 17))  # Current hour is within range

    def test_normal_range_screen_off(self):
        # Screen should be off outside on_hour and off_hour
        self.assertFalse(is_screen_on(8, 9, 17))  # Current hour is before range
        self.assertFalse(is_screen_on(18, 9, 17))  # Current hour is after range

    def test_overnight_range_screen_on(self):
        # Screen should be on for overnight ranges
        self.assertTrue(is_screen_on(23, 22, 6))  # Current hour is within range
        self.assertTrue(is_screen_on(2, 22, 6))  # Current hour is within range

    def test_overnight_range_screen_off(self):
        # Screen should be off outside overnight ranges
        self.assertFalse(is_screen_on(21, 22, 6))  # Current hour is before range
        self.assertFalse(is_screen_on(7, 22, 6))  # Current hour is after range

    def test_same_on_and_off_hour(self):
        # Screen should always be off if on_hour == off_hour
        self.assertFalse(is_screen_on(9, 9, 9))  # Any hour should return False

    def test_edge_cases(self):
        # Test edge cases where current_hour is exactly on the boundary
        self.assertTrue(is_screen_on(9, 9, 17))  # Current hour is exactly on on_hour
        self.assertFalse(is_screen_on(17, 9, 17))  # Current hour is exactly on off_hour
        self.assertTrue(
            is_screen_on(22, 22, 6)
        )  # Current hour is exactly on on_hour (overnight)
        self.assertFalse(
            is_screen_on(6, 22, 6)
        )  # Current hour is exactly on off_hour (overnight)


if __name__ == "__main__":
    unittest.main()
