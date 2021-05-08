
from datetime import datetime, timedelta, time, timezone
import pytz
from tasks.tasks import tesla_start_charging, tesla_stop_charging, test_connection

TIMEZONE = pytz.timezone("Europe/London")


now = datetime.utcnow()
start = now + timedelta(seconds=5)
end = start + timedelta(seconds=30)

tesla_start_charging.apply_async(eta=start)
tesla_stop_charging.apply_async(eta=end)

test_connection.delay()
