import logging

from celery import Celery

from config import *
from octopus import OctopusClient
from insights import EnergyPlanner, EnergyUsage
from messaging import notify_users_of_prices
from tesla import TeslaAPIClient

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
def daily_user_notification():
    notify_users_of_prices(hours=3, show_graph=False)

