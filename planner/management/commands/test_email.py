from django.core.management.base import BaseCommand

from planner.messaging import notify_users_of_prices


class Command(BaseCommand):
    def handle(self, *args, **options):
        notify_users_of_prices()
