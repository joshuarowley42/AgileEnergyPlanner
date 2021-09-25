from datetime import timedelta

from .octopus_api import OctopusAPIClient
from planner.models import EnergyPrices, EnergyUsage


def cached_time_series(model, super_func, start_time, end_time):
    if end_time is not None:
        r = model.objects.filter(time__gte=start_time, time__lte=end_time).order_by('time')
    else:
        r = model.objects.filter(time__gte=start_time).order_by('time')

    existing_data = {row.time: row.data for row in r}

    new_data = {}

    if existing_data:
        # If we have some data in the requested range, just get what we need

        # Missing data in the middle
        periods = sorted(existing_data.keys())
        for i in range(len(periods) - 1):
            if periods[i] + timedelta(minutes=30) != periods[i + 1]:
                new_data |= super_func(
                    start_time=periods[i] + timedelta(minutes=30),
                    end_time=periods[i + 1])

        # Missing data at the start
        earliest_data = min(existing_data.keys())
        if earliest_data > start_time:
            new_data |= super_func(
                start_time=start_time,
                end_time=earliest_data)
        # Missing data at the end
        latest_data = max(existing_data.keys())
        if end_time is None or latest_data < end_time:
            new_data |= super_func(
                start_time=latest_data + timedelta(minutes=30),
                end_time=end_time)

    else:
        new_data = super_func(
            start_time=start_time,
            end_time=end_time)

    if new_data:
        for period_start in new_data:
            existing_data[period_start] = new_data[period_start]
            model(time=period_start,
                  price=new_data[period_start]).save()

    return existing_data


class OctopusClient(OctopusAPIClient):
    def get_elec_price(self, start_time, end_time=None):
        return cached_time_series(EnergyPrices, super().get_elec_price,
                                  start_time, end_time)

    def get_elec_usage(self, start_time, end_time=None):
        return cached_time_series(EnergyUsage, super().get_elec_usage,
                                  start_time, end_time)
