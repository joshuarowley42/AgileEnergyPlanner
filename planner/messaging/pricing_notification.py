import logging
from datetime import datetime, timezone
from config import *

from ..common import energy_planner
from ..insights.data_tools import format_short_date, format_short_date_range, start_of_current_period
from ..insights.visualisation_tools import plot_svg
from ..models import EmailLog
from .email import send_email

logging.getLogger().setLevel(logging.INFO)


def notify_users_of_prices(hours=3):
    """ User notification for best and worst prices.

    This function finds the best, and worst, times to use energy and also gives some
    other useful info. It emails that information to the users defined in the config.

    The idea is that it can be sent on to those living in the property so they can
    plan usage (e.g. when to do the laundry).

    It will optionally show an interactive graph - that will prevent the email from
    being sent.

    :param hours: The size of the "best" and "peak" slots.
    :return: None
    """
    now = datetime.now(tz=timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    r = EmailLog.objects.filter(time__gte=start_of_today).first()

    if r:
        logging.info("Email already sent today. Skipping")
        return False

    if not energy_planner.tomorrows_data_available:
        logging.info("Data not yet available for tomorrow. Skipping")
        return False

    ep_pd = energy_planner.ep_df()
    gp_pd = energy_planner.gp_from_now_df()

    # Get best stop & start times for Electric usage.
    best_starts_and_stops, best_price = energy_planner.plan_usage_periods(hours=3, mode="best")
    peak_starts_and_stops, peak_price = energy_planner.plan_usage_periods(hours=3, mode="peak")

    # Get an HTML graph of the same

    best_time = format_short_date_range(best_starts_and_stops[0])
    peak_time = format_short_date_range(peak_starts_and_stops[0])
    average = energy_planner.average_price()
    average_excluding_peak = energy_planner.average_price(excluded_periods=peak_starts_and_stops)

    svg = plot_svg([ep_pd, gp_pd], starts_and_stops=best_starts_and_stops + peak_starts_and_stops)
    price_message = f"Best 3h {best_time} - {best_price:.2f}" \
                    f"Peak 3h {peak_time} - {peak_price:.2f}" \
                    f"Average all-day {average:.2f}" \
                    f"Average outside peak {average_excluding_peak:.2f}"

    if not DEV_MODE:
        now = format_short_date(start_of_current_period().astimezone(TIMEZONE))
        send_email(subject=f"Electricity Prices - From {now}",
                   message=price_message, svg=svg)

        # Log the email was sent so we don't send it again when this function gets called again.
        EmailLog(time=datetime.now(tz=timezone.utc)).save()
    else:
        logging.info("Will not send emails with DEV_MODE mode on.")

    return None
