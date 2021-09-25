from tesla import TeslaAPIClient
from planner.messaging import notify_users_of_prices

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


def tesla_start_charging():
    t = get_tesla()
    t.start_charging()


def tesla_stop_charging():
    t = get_tesla()
    t.stop_charging()


def water_start_heating():
    hot_water_elec.on()


def water_stop_heating():
    hot_water_elec.off()


def daily_user_notification():
    notify_users_of_prices()
