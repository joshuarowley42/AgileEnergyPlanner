import logging

from datetime import datetime, timedelta, timezone

from config import *
from tesla import TeslaAPIClient
from octopus import OctopusClient
from insights import EnergyPlanner
from insights.data_tools import format_short_date_range
#from tasks.tasks import tesla_start_charging, tesla_stop_charging

from data_store import session, CarChargingSession, CarChargingPeriod

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


def plan_charging(departure_hour,
                  hours_needed=None,
                  max_cost=None,
                  clear_existing=False,
                  tz=TIMEZONE):

    now = datetime.now(tz=tz)
    departure = now.replace(hour=departure_hour,
                            minute=0,
                            second=0, microsecond=0)

    if now.hour > departure_hour:
        departure = departure + timedelta(days=1)

    charges = session.query(CarChargingSession)\
        .where(CarChargingSession.departure >= now.astimezone(timezone.utc))\
        .all()

    if charges:
        logging.warning("There area already {} charges scheduled.".format(len(charges)))
        if clear_existing:
            for charge in charges:
                session.delete(charge)
                session.commit()
        else:
            logging.error("Aborting due to existing charges")
            return None

    charge_session = CarChargingSession(departure=departure)
    session.add(charge_session)

    charging_periods = planner.plan_car_charging(departure=departure,
                                                 hours_needed=hours_needed,
                                                 max_cost=max_cost,
                                                 graph=True)

    for period in charging_periods:
        logging.info("Charge Period: {}".format(format_short_date_range(period)))
        start, stop = period
        scheduled = False
        if not DEV_MODE:
            tesla_start_charging.apply_async(eta=start)
            tesla_stop_charging.apply_async(eta=stop)
            scheduled = True

        period = CarChargingPeriod(start_time=start,
                                   stop_time=stop,
                                   scheduled=scheduled)
        session.add(period)
    session.commit()

    logging.info("Charging planned.")
