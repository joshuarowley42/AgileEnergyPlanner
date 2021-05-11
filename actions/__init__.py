"""Quickly call functions

The actions module takes care of the messy setup required to perform basic actions that
mostly rely on functions in the insights module.

ToDo: Should this module really be separate from insights?
"""

from .user_communications import notify_users_of_prices
from .car_charging import plan_charging
