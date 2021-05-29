from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from tzlocal import get_localzone

from AgileEnergy.celery import app

from .models import CarChargingSession
from .tasks import tesla_start_charging, tesla_stop_charging

from .insights.data_tools import format_short_date, format_short_date_range, start_of_current_period
from .insights.visualisation_tools import plot_html

from .common import energy_planner


def index(request):
    # Get Gas and Electric Prices
    ep_pd = energy_planner.ep_df()
    gp_pd = energy_planner.gp_from_now_df()

    # Get best stop & start times for Electric usage.
    best_starts_and_stops, best_price = energy_planner.plan_usage_periods(hours=3, mode="best")
    peak_starts_and_stops, peak_price = energy_planner.plan_usage_periods(hours=3, mode="peak")

    # Get an HTML graph of the same

    now_ep = ep_pd.values[0][0]
    now_time = format_short_date(ep_pd.index[0])
    best_time = format_short_date_range(best_starts_and_stops[0])
    peak_time = format_short_date_range(peak_starts_and_stops[0])
    average = energy_planner.average_price()
    average_excluding_peak = energy_planner.average_price(excluded_periods=peak_starts_and_stops)

    graph = plot_html([ep_pd, gp_pd], starts_and_stops=best_starts_and_stops + peak_starts_and_stops)
    price_data = [("Current Price", now_time, f"{now_ep:.2f}"),
                  ("Best 3h", best_time, f"{best_price:.2f}"),
                  ("Peak 3h", peak_time, f"{peak_price:.2f}"),
                  ("Average", "all-day", f"{average:.2f}"),
                  ("Average", "outside peak", f"{average_excluding_peak:.2f}")]

    return render(request, 'index.html', context={"graph": graph,
                                                  "price_data": price_data})


def plan_charge(request):
    now = datetime.now(tz=get_localzone())

    future_sessions = CarChargingSession.objects.filter(departure__gte=now, scheduled=True)
    if future_sessions:
        assert len(future_sessions) == 1, "Somehow, there are 2 sessions planned!?"
        return redirect('/charge/session/{}'.format(future_sessions[0].pk))

    departure_hour = int(request.GET.get("departure_hour", 8))
    hours_needed = float(request.GET.get("hours_needed", 2))
    max_cost = int(request.GET.get("max_cost", 15))

    now = datetime.now(tz=get_localzone())
    ep_pd = energy_planner.ep_df()

    departure = now.replace(hour=departure_hour,
                            minute=0,
                            second=0, microsecond=0)

    if now.hour > departure_hour:
        departure = departure + timedelta(days=1)

    charge_session = energy_planner.plan_car_charging(departure=departure,
                                                      hours_needed=hours_needed,
                                                      max_cost=max_cost)
    starts_and_stops = [(s.start_time, s.stop_time) for s in charge_session.carchargingperiod_set.all()]

    graph = plot_html([ep_pd], starts_and_stops=starts_and_stops, end_marker=departure)

    session_config = {
        "departure_hour": departure_hour,
        "hours_needed": hours_needed,
        "max_cost": max_cost,
    }

    return render(request, 'plan_charge.html', context={"graph": graph,
                                                        "session_config": session_config,
                                                        "charge_session": charge_session})


def schedule_charge(request, session_id):
    charge_session = CarChargingSession.objects.get(pk=session_id)

    for period in charge_session.carchargingperiod_set.all():
        period.start_task_id = tesla_start_charging.apply_async(eta=period.start_time).id
        period.stop_task_id = tesla_stop_charging.apply_async(eta=period.stop_time).id
    charge_session.scheduled = True
    charge_session.save()

    return redirect("/charge")


def show_charge(request, session_id):
    charge_session = CarChargingSession.objects.get(pk=session_id)

    starts_and_stops = [(s.start_time, s.stop_time) for s in charge_session.carchargingperiod_set.all()]

    start_time = min(starts_and_stops[0][0], start_of_current_period())

    ep_pd = energy_planner.ep_df(start_time=start_time)
    graph = plot_html([ep_pd], starts_and_stops=starts_and_stops, end_marker=charge_session.departure)

    return render(request, 'show_charge.html', context={"graph": graph,
                                                        "charge_session": charge_session})


def cancel_charge(request, session_id):
    charge_session = CarChargingSession.objects.get(pk=session_id)

    for period in charge_session.carchargingperiod_set.all():
        app.control.revoke(period.start_task_id)
        app.control.revoke(period.stop_task_id)

    charge_session.scheduled = False
    charge_session.save()
    return redirect("/charge")
