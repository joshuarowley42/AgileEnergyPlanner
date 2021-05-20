from datetime import datetime, timedelta, timezone
from flask import request, jsonify

from flask_ui import app

from config import *
from octopus import OctopusClient
from tesla import TeslaAPIClient
from insights import EnergyPlanner
from insights.visualisation_tools import plot_html

from data_store import session, CarChargingSession, CarChargingPeriod

from tasks import tesla_start_charging, tesla_stop_charging, water_stop_heating, water_start_heating

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


# Step 1 - Plan a charge. This will save a session in the DB
@app.route("/charge/plan_session")
def plan_charge():
    departure_hour = int(request.args.get("departure", 8))
    hours_needed = float(request.args.get("hours", None))
    max_cost = int(request.args.get("max_cost", 15))

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

    # Save to DB
    charge_session = CarChargingSession(departure=departure)
    session.add(charge_session)
    session.flush()

    for period in charging_periods:
        start, stop = period
        scheduled = False
        period = CarChargingPeriod(start_time=start,
                                   stop_time=stop,
                                   scheduled=scheduled,
                                   parent_id=charge_session.id)
        session.add(period)
    session.commit()

    return html


# Step 2 - Review the sessions.
@app.route("/charge/show_sessions")
def show_charges():
    now = datetime.now()

    charging_sessions = session.query(CarChargingSession) \
        .where(CarChargingSession.departure >= now.astimezone(timezone.utc)) \
        .all()

    detailed_session_list = []
    for charging_session in charging_sessions:
        periods = session.query(CarChargingPeriod)\
            .where(CarChargingPeriod.parent_id == charging_session.id)\
            .all()
        detailed_session_list.append((charging_session.as_dict(), [p.as_dict() for p in periods]))

    return jsonify(detailed_session_list)


# Step 3a - Commit car-charging sessions to the celery schedule.
@app.route("/charge/schedule_session/<charge_session_id>")
def schedule_charge_periods(charge_session_id):
    charge_periods = session.query(CarChargingPeriod) \
        .where(CarChargingPeriod.parent_id == charge_session_id) \
        .all()

    periods_scheduled = []

    for charge_period in charge_periods:
        start = charge_period.start_time
        stop = charge_period.stop_time
        if not DEV_MODE and not charge_period.scheduled:
            tesla_start_charging.apply_async(eta=start)
            tesla_stop_charging.apply_async(eta=stop)
            charge_period.scheduled = True
            session.commit()
            periods_scheduled.append(charge_period.as_dict())

    return jsonify(periods_scheduled)


# Step 3b - Commit hot-water sessions to the celery schedule.
# TODO - clearly planning should be separate. This is MVP grade stuff.
@app.route("/hot_water/schedule_session/<charge_session_id>")
def schedule_hot_water_periods(charge_session_id):
    charge_periods = session.query(CarChargingPeriod) \
        .where(CarChargingPeriod.parent_id == charge_session_id) \
        .all()

    periods_scheduled = []

    for charge_period in charge_periods:
        start = charge_period.start_time
        stop = charge_period.stop_time
        if not DEV_MODE and not charge_period.scheduled:
            water_start_heating.apply_async(eta=start)
            water_stop_heating.apply_async(eta=stop)
            charge_period.scheduled = True
            session.commit()
            periods_scheduled.append(charge_period.as_dict())

    return jsonify(periods_scheduled)