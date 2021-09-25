from django.core.management.base import BaseCommand

from planner.models import SystemScheduleTasks
from datetime import datetime, timezone

from planner.tasks import tesla_start_charging, tesla_stop_charging, water_start_heating, water_stop_heating
import logging

functions = [tesla_start_charging, tesla_stop_charging, water_start_heating, water_stop_heating]
functsion = [f.__name__ for f in functions]

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = datetime.now(tz=timezone.utc)

        tasks = SystemScheduleTasks.objects.filter(action_time__lte=now, completed=False).all()

        for task in tasks:
            logging.info(f"Executing {task.function}")
            try:
                assert t
                exec(f"{task.function}()")
            except Exception as e:
                logging.error(f"Failed executing {task.function}. {e}")
