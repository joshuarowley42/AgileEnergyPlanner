from AgileEnergy.celery import app
from tesla import TeslaAPIClient
from planner.messaging import notify_users_of_prices

from celery.schedules import crontab
from gpiozero import DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

from config import *

hot_water_elec = DigitalOutputDevice(PI_ELEC_WATER_HEATER_PIN, pin_factory=PiGPIOFactory(host=PI_IP))
nest_override = DigitalOutputDevice(PI_NEST_OVERRIDE_PIN, pin_factory=PiGPIOFactory(host=PI_IP))
hot_water_gas = DigitalOutputDevice(PI_GAS_WATER_HEATER_PIN, pin_factory=PiGPIOFactory(host=PI_IP))
hot_water_gas.close()

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
    hot_water_elec.on()


@app.task
def water_stop_heating():
    hot_water_elec.off()


@app.task
def daily_user_notification():
    notify_users_of_prices()
