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

        # Before 1600 (UK) - we know we won't have data for anything beyond 2200 (UTC) tonight.
        if now.astimezone().hour < 16 and start_time > now.replace(hour=21, minute=30,
                                                                   second=0, microsecond=0):
            return {}

        return super().get_elec_price(start_time=start_time,
                                      end_time=end_time)
