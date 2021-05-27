from django.test import TestCase

from planner.messaging import notify_users_of_prices
from config import DEV_MODE


class NotificationEmail(TestCase):
    def setUp(self):
        assert DEV_MODE, "Must be in DEV_MODE, otherwise user will get email"

    def test_emails(self):
        png, price_message = notify_users_of_prices(test_mode=True)
        self.assertTrue(bool(png))
        self.assertTrue("Average outside peak" in price_message)
