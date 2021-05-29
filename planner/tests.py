from django.test import TestCase

from planner.messaging import notify_users_of_prices
from planner.common import energy_planner
from config import DEV_MODE


class NotificationEmail(TestCase):
    def setUp(self):
        assert DEV_MODE, "Must be in DEV_MODE, otherwise user will get email"

    def test_emails(self):
        response = notify_users_of_prices(test_mode=True)

        if not energy_planner.tomorrows_data_available:
            # If tomorrows data isn't available, it should be false
            self.assertFalse(response)
        else:
            png, price_message = response
            self.assertTrue(bool(png))
            self.assertTrue("Average outside peak" in price_message)
