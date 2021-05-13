
import logging
from datetime import datetime, timezone

from config import *
from octopus import OctopusClient
from insights import EnergyPlanner
from insights.data_tools import format_short_date_range, start_of_current_period, format_short_date
from messaging import send_email
from data_store import EmailLog, session


energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

planner = EnergyPlanner(energy_provider)

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

    r = session.query(EmailLog) \
        .where(EmailLog.time >= start_of_today)\
        .first()

    if r:
        logging.info("Email already sent today. Skipping")
        return False

    if not planner.tomorrows_data_available:
        logging.info("Data not yet available for tomorrow. Skipping")
        return False

    average = planner.average_price()

    # Get good times to do a 3h load of dishes or clothes
    best_starts_and_stops, best_price = planner.plan_usage_periods(hours=hours, mode="best")
    best_time = format_short_date_range(best_starts_and_stops[0])

    # Get peak 3h slot (normally gonna be 1600-1900)
    peak_starts_and_stops, peak_price = planner.plan_usage_periods(hours=hours, mode="peak")
    peak_time = format_short_date_range(peak_starts_and_stops[0])

    average_excluding_peak = planner.average_price(excluded_periods=peak_starts_and_stops)

    price_message = f"BEST 3h {best_time} - {best_price:.2f}p/kWh\n" \
                    f"PEAK 3h {peak_time} - {peak_price:.2f}p/kWh\n" \
                    f"Average all-day: {average:.2f}p/kWh\n" \
                    f"Average outside peak: {average_excluding_peak:.2f}p/kWh\n"

    logging.info(price_message)

    # Handy to have this outside the below if so that you can inspect the png.
    png = planner.plot_future_prices(starts_and_stops=best_starts_and_stops + peak_starts_and_stops,
                                     return_file=True)

    if not DEV_MODE:
        now = format_short_date(start_of_current_period().astimezone())
        send_email(subject=f"Electricity Prices - From {now}",
                   message=price_message, png=png)

        # Log the email was sent so we don't send it again when this function gets called again.
        session.add(EmailLog(time=datetime.now(tz=timezone.utc)))
        session.commit()
    else:
        logging.info("Will not send emails with DEV_MODE mode on.")

    return None
