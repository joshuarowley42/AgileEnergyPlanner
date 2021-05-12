from datetime import datetime, timezone, timedelta

from .octopus_api import OctopusAPIClient
from data_store import EnergyPrices, session


class OctopusClient(OctopusAPIClient):
    def get_elec_price(self, start_time, end_time=None):

        r = session.query(EnergyPrices)\
            .where(EnergyPrices.time >= start_time)\
            .order_by(EnergyPrices.time.asc())\
            .all()

        prices_dict = {row.time_utc: row.price for row in r}

        new_prices = {}

        if prices_dict:
            # If we have some data in the requested range, just get what we need

            # Missing data in the middle
            periods = sorted(prices_dict.keys())
            for i in range(len(periods) - 1):
                if periods[i] + timedelta(minutes=30) != periods[i+1]:
                    new_prices |= self.check_for_new_prices(start_time=periods[i] + timedelta(minutes=30),
                                                            end_time=periods[i+1])

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
            for time in new_prices:
                prices_dict[time] = new_prices[time]
                session.add(EnergyPrices(time=time,
                                         price=new_prices[time]))
            session.commit()

        return prices_dict

    def check_for_new_prices(self, start_time, end_time):
        """ Makes get_elec_price lazy.

        This function adds a little contextual knowledge about what data
        is likely to be available before just heading off to get it blindly.
        """

        now = datetime.now(tz=timezone.utc)
        if start_time.day < now.astimezone().day:
            # There will surely be historical data available
            return super().get_elec_price(start_time=start_time,
                                          end_time=end_time)

        if start_time.day > now.astimezone().day:
            # Already have tomorrow's data
            return {}

        if now.astimezone().hour >= 16:
            # After 1600, we might expect tomorrow's prices.
            # Given that we don't already have that data, go and check for it!
            return super().get_elec_price(start_time=start_time,
                                          end_time=end_time)
