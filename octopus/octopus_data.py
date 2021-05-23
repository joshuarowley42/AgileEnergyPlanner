from datetime import datetime, timezone, timedelta

from config import *

from .octopus_api import OctopusAPIClient
from planner.models import EnergyPrices


class OctopusClient(OctopusAPIClient):
    def get_elec_price(self, start_time, end_time=None):
        r = EnergyPrices.objects.filter(time__gte=start_time).order_by('time')

        prices_dict = {row.time: row.price for row in r}

        new_prices = {}

        if prices_dict:
            # If we have some data in the requested range, just get what we need

            # Missing data in the middle
            periods = sorted(prices_dict.keys())
            for i in range(len(periods) - 1):
                if periods[i] + timedelta(minutes=30) != periods[i + 1]:
                    new_prices |= self.check_for_new_prices(start_time=periods[i] + timedelta(minutes=30),
                                                            end_time=periods[i + 1])

            # Missing data at the start
            earliest_data = min(prices_dict.keys())
            if earliest_data > start_time:
                new_prices |= self.check_for_new_prices(start_time=start_time,
                                                        end_time=earliest_data)
            # Missing data at the end
            latest_data = max(prices_dict.keys())
            if end_time is None or latest_data < end_time:
                new_prices |= self.check_for_new_prices(start_time=latest_data + timedelta(minutes=30),
                                                        end_time=end_time)

        else:
            new_prices = self.check_for_new_prices(start_time=start_time,
                                                   end_time=end_time)

        if new_prices:
            for period_start in new_prices:
                prices_dict[period_start] = new_prices[period_start]
                EnergyPrices(time=period_start,
                             price=new_prices[period_start]).save()

        return prices_dict

    def check_for_new_prices(self, start_time, end_time):
        """ Makes get_elec_price lazy.

        This function adds a little contextual knowledge about what data
        is likely to be available before just heading off to get it blindly.
        """
        now = datetime.now(tz=timezone.utc)

        # We will never have more data than this
        if start_time > now.replace(hour=21, minute=30,
                                    second=0, microsecond=0) + timedelta(days=1):
            return {}

        # Before 1600 (UK) - we know we won't have data for anything beyond 2200 (UTC) tonight.
        if now.astimezone(TIMEZONE).hour < 16 and start_time > now.replace(hour=21, minute=30,
                                                                           second=0, microsecond=0):
            return {}

        return super().get_elec_price(start_time=start_time,
                                      end_time=end_time)
