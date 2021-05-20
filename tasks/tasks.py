import logging

from celery import Celery
from celery.schedules import crontab

from config import *
from messaging import notify_users_of_prices
from tesla import TeslaAPIClient

from gpiozero import DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

hot_water_relay = DigitalOutputDevice(PI_HEATER_PIN, pin_factory=PiGPIOFactory(host=PI_IP))


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
def water_start_heating():
    hot_water_relay.on()


@app.task
def water_stop_heating():
    hot_water_relay.off()


@app.task
def daily_user_notification():
    notify_users_of_prices(hours=3)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every 10 minutes from 1500 UTC (1600 BST) to 2000 UTC (2100 BST)
    sender.add_periodic_task(
        crontab(hour='15-20', minute='*/10'),
        daily_user_notification.s(),
    )
