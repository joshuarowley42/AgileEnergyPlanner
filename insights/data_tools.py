
from datetime import timedelta, datetime, timezone
import pandas

from config import *


def find_contiguous_periods(target_times: pandas.DataFrame):
    """
    Get start & end times for contiguous periods

    :param target_times: List of start times for 30m slots..
    """

    contiguous_periods = []

    # Sort them to make sure they are in date order, or things break
    target_times = target_times.sort_values()

    if not len(target_times):
        return contiguous_periods

    start = target_times[0]
    last_period = target_times[0]
    for t in target_times[1:]:
        if t != last_period + timedelta(minutes=30):
            period = (start, last_period + timedelta(minutes=30))
            contiguous_periods.append(period)
            start = t
        last_period = t
    period = (start, last_period + timedelta(minutes=30))
    contiguous_periods.append(period)

    return contiguous_periods


def start_of_current_period():
    """
    Quickly get the start time of the current period.
    """

    now = datetime.now(tz=timezone.utc)
    previous_period = now.replace(minute=now.minute - (now.minute % 30),
                                  second=0,
                                  microsecond=0)

    return previous_period


def format_short_date(dt: datetime, tz=TIMEZONE):
    """
    Get a short-format date time localised to specified timezone returned as a string

    :param dt: datetime
    :param tz: Timezone
    """

    dt_local = dt.astimezone(tz)
    return datetime.strftime(dt_local, "%d/%m %H%M")


def format_short_date_range(ss: (datetime, datetime), tz=TIMEZONE):
    """
    Get a short-format date/time range localised to the specified timezone returned as a string

    :param ss: Start Stop - tuple of datetimes
    :param tz: Timezone
    """

    (start, stop) = ss

    start_local = start.astimezone(tz)
    stop_local = stop.astimezone(tz)
    date_string = datetime.strftime(start_local, "%a %d %H%M")
    date_string += datetime.strftime(stop_local, "-%H%M")
    if start.day != stop.day:
        assert stop.day == start.day + 1, "Stop day must be same day, or the day after, start day."
        date_string += "*"  # * indicates next day
    return date_string
