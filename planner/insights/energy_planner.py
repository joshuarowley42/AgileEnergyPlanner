from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone
import pandas
import logging

from ..models import CarChargingSession, CarChargingPeriod, SystemStatus

from .data_tools import find_contiguous_periods, start_of_current_period, drop_periods_from_df
from .exceptions import NoSolutions, NoCrystalBall

from django.conf import settings


class EnergyPlanner:
    def __init__(self,
                 energy_provider,
                 car=None):

        self.energy_provider = energy_provider
        self.car = car

    def ep_df_from_now(self,
                       excluded_periods: list[(datetime, datetime)] = None,
                       column_name: str = 'electricity price') -> pandas.DataFrame:

        start_time = start_of_current_period()
        ep = self.energy_provider.get_elec_price(start_time)
        ep_pd = pandas.DataFrame.from_dict(ep, orient="index", columns=[column_name]).sort_index()

        if excluded_periods is not None:
            ep_pd = drop_periods_from_df(ep_pd, excluded_periods)

        return ep_pd

    def gp_df_from_now(self,
                       excluded_periods: (datetime, datetime) = None,
                       column_name: str = 'gas price') -> pandas.DataFrame:

        start_time = start_of_current_period()
        gp = self.energy_provider.get_gas_price(start_time)
        gp_pd = pandas.DataFrame.from_dict(gp, orient="index", columns=[column_name]).sort_index()

        if excluded_periods is not None:
            gp_pd = drop_periods_from_df(gp_pd, excluded_periods)

        return gp_pd

    @property
    def tomorrows_data_available(self) -> bool:
        """
        Check if data is available for tomorrow.

        Note that the get_elec_price (called in ep_from_now) doesn't make an API call unless there is
        a chance that the data is available, so there is no penalty for calling this at any time of day.

        :return: bool
        """
        now = datetime.now(tz=timezone.utc)
        prices_dict = self.ep_df_from_now()
        last_time = max(prices_dict.index)
        if last_time.day > now.day:
            return True
        return False

    def average_price(self,
                      excluded_periods: (datetime, datetime) = None) -> float:
        """
        Get average electricity prices from "now". Optionally exclude some periods from the averages.

        :param excluded_periods: List of periods (tuples of start and stop times) excluded
        :return:
        """

        ep_pd = self.ep_df_from_now(excluded_periods=excluded_periods)

        return ep_pd.mean()[0]

    def plan_usage_periods(self,
                           hours: float = 2,
                           mode: str = "best",
                           excluded_periods: (datetime, datetime) = None) -> (datetime, datetime):
        """
        For a given length of time - find contiguous periods that have the
        lowest "best" (or highest "peak") average price.

        Useful to plan times to use (or not use) energy. Clearly assumes equal
        usage over the period which may well not be the case.

        :param excluded_periods: (start, stop) periods to exclude from the averages
        :param hours: Size of the window
        :param mode: "best" or "peak"
        :return: (start, stop), mean price
        """

        assert hours * 2 % 1 == 0, "smallest increment of hours is 0.5"
        periods_needed = int(hours * 2)

        assert mode in ["best", "peak"], "'mode' must be 'best' or 'peak'"

        ep_pd = self.ep_df_from_now(excluded_periods=excluded_periods)

        window = ep_pd.rolling(timedelta(minutes=30) * periods_needed, min_periods=periods_needed).mean()
        # THe window is backwards looking, so the result will be for the start of the last period.
        # Hence, usage should stop 30m later, start calculated based on end.
        cheapest = window.min()[0]
        cheapest_stop = window.idxmin()[0] + timedelta(minutes=30)
        cheapest_start = cheapest_stop - timedelta(minutes=30) * periods_needed

        dearest = window.max()[0]
        dearest_stop = window.idxmax()[0] + timedelta(minutes=30)
        dearest_start = dearest_stop - timedelta(minutes=30) * periods_needed

        if mode == "best":
            starts_stops = [(cheapest_start, cheapest_stop)]
            return starts_stops, cheapest

        elif mode == "peak":
            starts_stops = [(dearest_start, dearest_stop)]
            return starts_stops, dearest

    def plan_car_charging(self,
                          departure: datetime = None,
                          hours_needed: float = None,
                          max_cost: float = None) -> [(datetime, datetime)]:
        """
        Find the cheapest set of half-hour segments to charge car. Pass in a departure time
        (or will assume you want to depart at the end of the data available from energy API).

        Assumes 100% usage across all hours needed (i.e. no probability distribution)

        :param departure: Target departure time. If not provided, will use end time of price data returned by API.
        :param hours_needed: Hours of charging wanted. If not provided, will use Tesla API to calculate based on SOC.
        :param max_cost: Don't pay more than this per kWh.
        :return:
        """

        if hours_needed is None:
            assert self.car is not None, "No car, either specific hours_needed, or re-initiate class with car."
            periods = int(self.car.hours_to_target_soc * 2) + 1
        else:
            assert hours_needed * 2 % 1 == 0, "smallest increment of hours is 0.5"
            periods = int(hours_needed * 2)

        ep_pd = self.ep_df_from_now()
        data_end = max(ep_pd.index)

        if departure is not None:
            assert departure.tzinfo, "'before' must be supplied timezone aware"
            if departure > data_end:
                raise NoCrystalBall(f"No data for requested 'before' time. Max: {data_end}")
            ep_pd = ep_pd.loc[:departure - timedelta(minutes=30)]
        else:
            logging.warning(f"No 'before' specified. Using end-date of {data_end}")

        if max_cost is not None:
            ep_pd = ep_pd.where(ep_pd <= max_cost).dropna()

        if not len(ep_pd):
            raise NoSolutions("Sorry, no charging options given inputs.")

        target_times = ep_pd.sort_values(by='electricity price')[:periods].sort_index().index

        charging_periods = find_contiguous_periods(target_times)

        average_cost = sum([ep_pd.loc[time] for time in target_times])[0] / len(target_times)
        charge_session = CarChargingSession(departure=departure,
                                            average_cost=average_cost,
                                            scheduled=False)
        charge_session.save()

        for period in charging_periods:
            start, stop = period
            period = CarChargingPeriod(start_time=start,
                                       stop_time=stop,
                                       parent=charge_session)
            period.save()

        return charge_session

    def plan_water_heating(self):

        """This is supposed to be executed once per day, as soon as we have new data available.
        Currently it will make sure we get in 1h of HW heating between
        * 2300 - 0600*  (Phase A)
        * 1000* - 1800* (Phase B)

        Where * means tomorrow.

        For now - it assumes uniform usage across the 1h period. Should be weighted so a cheaper 1st 30m is cheaper.
        """
        n = datetime.now(tz=get_localzone()).replace(minute=0,
                                                     second=0,
                                                     microsecond=0)
        phase_a = (n.replace(hour=23),
                   n.replace(hour=6) + timedelta(days=1))

        phase_b = (n.replace(hour=10) + timedelta(days=1),
                   n.replace(hour=18) + timedelta(days=1))

        system_status = SystemStatus.objects.get(id=settings.AE_SITE_ID)

        assert not system_status.hw_nest_override, "Nest must be overridden."

        if not self.tomorrows_data_available:
            raise NoCrystalBall("Can't plan before we have data for tomorrow.")

        ep_pd = self.ep_df_from_now()
        gp_pd = self.gp_df_from_now()
        gp_pd = gp_pd/settings.AE_GAS_EFFICIENCY    # Adjust gas price to account for boiler efficiency.

