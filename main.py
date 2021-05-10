# Agile Energy Planner

# This file is just an entry-point for development and testing.

from datetime import datetime, timedelta, timezone

from config import *
from tesla import TeslaAPIClient
from octopus import OctopusClient
from insights import EnergyPlanner, EnergyUsage
from insights.data_tools import format_short_date_range, start_of_current_period
from tasks.tasks import tesla_start_charging, tesla_stop_charging

energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
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
    depart_time = 8

    now = datetime.now(tz=TIMEZONE)
    depart = now.replace(hour=depart_time, minute=0, second=0)

    if now.hour > depart_time:
        depart = depart + timedelta(days=1)

    charging_periods = planner.plan_car_charging(departure=depart, hours_needed=5,
                                                 max_cost=15, graph=True)

    for period in charging_periods:
        print("Charge Period: {}".format(format_short_date_range(period)))
        start, stop = period
        if not DEV_MODE:
            tesla_start_charging.apply_async(eta=start)
            tesla_stop_charging.apply_async(eta=stop)

    print("Charging planned.")


def show_usage():
    start_time = datetime(year=2021,
                          month=4,
                          day=20, tzinfo=TIMEZONE)
    # Started Agile on 30th April

    usage.plot_usage_and_costs(start_time)





from data_store.models import EnergyPrices, session

if __name__ == "__main__":

    t = start_of_current_period()
    t = t.replace(minute=0, hour=23)
    to_delete = session.query(EnergyPrices).where(EnergyPrices.time >= t)
    for p in to_delete:
        session.delete(p)
    session.commit()
    a = energy_provider.get_elec_price(start_time=start_of_current_period())
    # notify_users_of_prices(show_graph=False)
    # show_usage()

    # tesla_journey()





