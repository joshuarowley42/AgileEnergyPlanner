
from celery import Celery
from datetime import datetime

from config import *
from octopus import OctopusClient
from insights import EnergyPlanner, EnergyUsage
from insights.data_tools import format_short_date_range, format_short_date
from tesla import TeslaAPIClient
from messaging import send_email

# Configure Celery
app = Celery('tasks.tasks',
             broker='redis://localhost',
             enable_utc=True,
             timezone="utc")
# This 24h timeout means that tasks can be queued (eta set) for up to 24h in the future.
# In theory the code works just fine without it, but tasks that are due to start outside
# whatever range is set risk being run multiple times (saw tasks run 10+ times before I
# put this in place). I believe this is a redis-specific issue and isn't a problem with
# RabbitMQ.
app.conf.broker_transport_options = {'visibility_timeout': 3600*24}


# Bring in our apps
energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

planner = EnergyPlanner(energy_provider)    # Don't need a car in the planner
usage = EnergyUsage(energy_provider)


def get_tesla():
    # The connection seems most robust if a new instance of the client is created each time.
    # Not entirely sure why.
    return TeslaAPIClient(TESLA_USERNAME,
                          TESLA_PASSWORD,
                          dry_run=DEV_MODE)


@app.task
def tesla_start_charging():
    t = get_tesla()
    t.start_charging()


@app.task
def tesla_stop_charging():
    t = get_tesla()
    t.stop_charging()


@app.task
def notify_users_of_prices(hours=3, show_graph=False):

    average = planner.average_price()

    # Get good times to do a 3h load of dishes or clothes
    best_starts_and_stops, best_price = planner.plan_usage_periods(hours=hours, mode="best")
    best_time = format_short_date_range(best_starts_and_stops[0])

    # Get peak 3h slot (normally gonna be 1600-1900)
    peak_starts_and_stops, peak_price = planner.plan_usage_periods(hours=hours, mode="peak")
    peak_time = format_short_date_range(peak_starts_and_stops[0])

    average_excluding_peak = planner.average_price(excluded_periods=peak_starts_and_stops)

    a = f"BEST 3h {best_time} - {best_price:.2f}p/kWh\n" \
        f"PEAK 3h {peak_time} - {peak_price:.2f}p/kWh\n" \
        f"Average all-day: {average:.2f}p/kWh\n" \
        f"Average outside peak: {average_excluding_peak:.2f}p/kWh\n"

    if show_graph:
        planner.plot_future_prices(starts_and_stops=best_starts_and_stops + peak_starts_and_stops)

    png = planner.plot_future_prices(starts_and_stops=best_starts_and_stops + peak_starts_and_stops,
                                     return_file=True)
    if not DEV_MODE:
        now = format_short_date(datetime.now(tz=TIMEZONE))
        send_email(subject=f"Electricity Prices - From {now}",
                   message=a, png=png)
    else:
        print(a)

