# Agile Energy Planner

# This file is just an entry-point for development and testing.

from datetime import datetime, timedelta, timezone

from config import *
from tesla import TeslaAPIClient
from octopus import OctopusAPIClient
from insights import EnergyPlanner, EnergyUsage
from insights.data_tools import format_short_date_range
from tasks.tasks import tesla_start_charging, tesla_stop_charging

energy_provider = OctopusAPIClient(username=OCTOPUS_USERNAME,
                                   zone=OCTOPUS_ZONE,
                                   e_mpan=OCTOPUS_ELEC_MPAN,
                                   e_msn=OCTOPUS_ELEC_MSN,
                                   g_mprn=OCTOPUS_GAS_MPRN,
                                   g_msn=OCTOPUS_GAS_MSN)

car = TeslaAPIClient(email=TESLA_USERNAME,
                     password=TESLA_PASSWORD,
                     dry_run=DEV_MODE)

planner = EnergyPlanner(energy_provider, car)
usage = EnergyUsage(energy_provider)

from tasks.tasks import notify_users_of_prices


def tesla_journey():
    # Plan charging for the Tesla
    depart_time = 16

    now = datetime.now(tz=TIMEZONE)
    depart = now.replace(hour=depart_time, minute=0, second=0)

    if now.hour > depart_time:
        depart = depart + timedelta(days=1)

    charging_periods = planner.plan_car_charging(departure=depart, hours_needed=2,
                                                 max_cost=15, graph=True)

    if not DEV_MODE:
        for period in charging_periods:
            print("Charge Period: {}".format(format_short_date_range(period)))
            start, stop = period
            tesla_start_charging.apply_async(eta=start)
            tesla_stop_charging.apply_async(eta=stop)

    print("Charging planned.")


def show_usage():
    start_time = datetime(year=2021,
                          month=4,
                          day=20, tzinfo=TIMEZONE)
    # Started Agile on 30th April

    usage.plot_usage_and_costs(start_time)





if __name__ == "__main__":

    notify_users_of_prices(show_graph=True)
    # show_usage()

    # tesla_journey()




