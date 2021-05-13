from flask_ui import app

from config import *
from octopus import OctopusClient
from insights import EnergyPlanner
from insights.visualisation_tools import plot_html


energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

planner = EnergyPlanner(energy_provider)


@app.route('/')
def index():
    # Get Gas and Electric Prices
    ep_pd = planner.ep_from_now_df()
    gp_pd = planner.gp_from_now_df()

    # Get best stop & start times for Electric usage.
    best_starts_and_stops, best_price = planner.plan_usage_periods(hours=3, mode="best")
    peak_starts_and_stops, peak_price = planner.plan_usage_periods(hours=3, mode="peak")

    # Get an HTML graph of the same
    html = plot_html([ep_pd, gp_pd], starts_and_stops=best_starts_and_stops + peak_starts_and_stops)

    return html
