from .insights import EnergyPlanner
from octopus import OctopusClient
from config import *

energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

planner = EnergyPlanner(energy_provider)