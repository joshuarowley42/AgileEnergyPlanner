
from datetime import datetime

from config import *
from octopus import OctopusClient
from insights import EnergyUsage

energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

usage = EnergyUsage(energy_provider)


def show_usage():
    start_time = datetime(year=2021,
                          month=4,
                          day=20, tzinfo=TIMEZONE)
    # Started Agile on 30th April

    usage.plot_usage_and_costs(start_time)
