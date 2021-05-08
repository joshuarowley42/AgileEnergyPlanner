from datetime import datetime
import pandas

from .visualisation_tools import show_plot


class EnergyUsage:
    def __init__(self, energy_provider):
        self.energy_provider = energy_provider

    def plot_usage_and_costs(self, start_time):
        """
        Show a plot of historic usage, and all costs available since that time.

        :param start_time:
        :return:
        """
        ep = self.energy_provider.get_elec_price(start_time=start_time)
        eu = self.energy_provider.get_elec_usage(start_time=start_time)
        gp = self.energy_provider.get_gas_price(start_time=start_time)
        gu = self.energy_provider.get_gas_usage(start_time=start_time)

        show_plot(ep=ep, gp=gp, eu=eu, gu=gu)

    def print_average_electricity_cost(self, start_time):
        """
        Based on consumption and variable prices - calculate the average cost paid for energy.

        Used this to understand if switching to Agile and making no optimisations to energy usage
        would cost more. It was about the same.

        :param start_time:
        :return:
        """
        ep = self.energy_provider.get_elec_price(start_time=start_time)
        eu = self.energy_provider.get_elec_usage(start_time=start_time)

        prices_pd_ep = pandas.DataFrame.from_dict(ep, orient="index", columns=['e_price'])
        prices_pd_eu = pandas.DataFrame.from_dict(eu, orient="index", columns=['e_usage'])

        electricity_cost = pandas.concat(
            [prices_pd_ep, prices_pd_eu],
            axis=1,
            copy=True
        )
        electricity_cost = electricity_cost.dropna()
        electricity_cost['e_cost'] = electricity_cost['e_price'] * electricity_cost['e_usage']

        usage = electricity_cost['e_usage'].sum()
        cost = electricity_cost['e_cost'].sum()
        average_price = cost / usage

        from_date = datetime.strftime(electricity_cost.index.min(), "%Y-%m-%d")
        to_date = datetime.strftime(electricity_cost.index.max(), "%Y-%m-%d")

        print(f"From {from_date} to {to_date}")
        print(f"Total usage: {usage}")
        print(f"Total cost: {cost}")
        print(f"Average £/kWh: {average_price}")
