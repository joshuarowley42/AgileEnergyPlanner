from datetime import datetime, timedelta
from flask import request

from flask_ui import app

from config import *
from octopus import OctopusClient
from tesla import TeslaAPIClient
from insights import EnergyPlanner
from insights.visualisation_tools import plot_html


energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)

car = TeslaAPIClient(email=TESLA_USERNAME,
                     password=TESLA_PASSWORD,
                     dry_run=DEV_MODE)

planner = EnergyPlanner(energy_provider, car)


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


@app.route("/charge/<int:departure_hour>")
def charge(departure_hour):
    hours_needed = request.args.get("hours", None)
    max_cost = request.args.get("max_cost", 15)

    now = datetime.now(tz=TIMEZONE)
    departure = now.replace(hour=departure_hour,
                            minute=0,
                            second=0, microsecond=0)

    if now.hour > departure_hour:
        departure = departure + timedelta(days=1)

    charging_periods = planner.plan_car_charging(departure=departure,
                                                 hours_needed=hours_needed,
                                                 max_cost=max_cost)

    ep_pd = planner.ep_from_now_df()
    html = plot_html([ep_pd], starts_and_stops=charging_periods)

    return html

