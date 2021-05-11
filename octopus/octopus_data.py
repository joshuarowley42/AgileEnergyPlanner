from datetime import datetime, timezone, timedelta

from .octopus_api import OctopusAPIClient
from data_store import EnergyPrices, session


class OctopusClient(OctopusAPIClient):
    def get_elec_price(self, start_time):

        r = session.query(EnergyPrices)\
            .where(EnergyPrices.time >= start_time)\
            .order_by(EnergyPrices.time.asc())\
            .all()

        prices_dict = {row.time_utc: row.price for row in r}
        if prices_dict:
            last_time = max(prices_dict.keys())
        else:
            last_time = start_time

        new_prices = self.check_for_new_prices(since=last_time)

        if new_prices:
            for time in new_prices:
                prices_dict[time] = new_prices[time]
                session.add(EnergyPrices(time=time,
                                         price=new_prices[time]))
            session.commit()

        return prices_dict

    def check_for_new_prices(self, since):
        now = datetime.now(tz=timezone.utc)
        if since.day < now.astimezone().day:
            # There will surely be historical data available
            return super().get_elec_price(since + timedelta(minutes=30))

        if since.day > now.astimezone().day:
            # Already have tomorrow's data
            return {}

        if now.astimezone().hour >= 16:
            # After 1600, we might expect tomorrow's prices.
            # Given that we don't already have that data, go and check for it!
            return super().get_elec_price(since + timedelta(minutes=30))
