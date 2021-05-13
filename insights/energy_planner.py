from datetime import datetime, timedelta, timezone
import pandas
import logging

from .data_tools import find_contiguous_periods, start_of_current_period
from .visualisation_tools import show_plot


def drop_periods_from_df(df: pandas.DataFrame,
                         periods: list[(datetime, datetime)]) -> pandas.DataFrame:

    periods_to_drop = []
    for period in periods:
        (start, stop) = period
        periods_to_drop += list(df[start:stop - timedelta(minutes=30)].index)
    df = df.drop(index=periods_to_drop)
    return df


class EnergyPlanner:
    def __init__(self, energy_provider, car=None):
        self.energy_provider = energy_provider
        self.car = car

    @property
    def ep_from_now(self) -> dict:
        """
        Get electricity prices starting from "now" - start of the current-half-hour period..
        """

        start_time = start_of_current_period()
        return self.energy_provider.get_elec_price(start_time)

    def ep_from_now_df(self,
                       excluded_periods: list[(datetime, datetime)] = None,
                       column_name: str = 'electricity price') -> pandas.DataFrame:

        start_time = start_of_current_period()
        ep = self.energy_provider.get_elec_price(start_time)
        ep_pd = pandas.DataFrame.from_dict(ep, orient="index", columns=[column_name]).sort_index()

        if excluded_periods is not None:
            ep_pd = drop_periods_from_df(ep_pd, excluded_periods)

        return ep_pd

    def gp_from_now_df(self,
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
        prices_dict = self.ep_from_now_df()
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

        ep_pd = self.ep_from_now_df(excluded_periods)

        return ep_pd.mean()[0]

    def plot_future_prices(self, **kwargs):
        """
        Plot a graph of future prices.
        :param kwargs:
        :return:
        """

        ep = self.ep_from_now
        return show_plot(ep=ep, **kwargs)

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

        ep_pd = self.ep_from_now_df(excluded_periods)

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

        ep_pd = self.ep_from_now_df()
        data_end = max(ep_pd.index)

        if departure is not None:
            assert departure.tzinfo, "'before' must be supplied timezone aware"
            assert departure <= data_end, f"No data for requested 'before' time. Max: {data_end}"
            ep_pd = ep_pd.loc[:departure - timedelta(minutes=30)]
        else:
            logging.warning(f"No 'before' specified. Using end-date of {data_end}")

        if max_cost is not None:
            ep_pd = ep_pd.where(ep_pd <= max_cost).dropna()

        target_times = ep_pd.sort_values(by='price')[:periods].sort_index().index

        charging_periods = find_contiguous_periods(target_times)

        return charging_periods
