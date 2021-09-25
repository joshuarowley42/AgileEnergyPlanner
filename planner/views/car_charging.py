from datetime import datetime, timedelta

from django.shortcuts import redirect, render
from tzlocal import get_localzone

from planner.common import energy_planner
from planner.insights.data_tools import start_of_current_period
from planner.insights.visualisation_tools import plot_html
from planner.models import CarChargingSession, SystemScheduleTasks
from planner.tasks import tesla_start_charging, tesla_stop_charging


def plan_charge(request):
    now = datetime.now(tz=get_localzone())

    future_sessions = CarChargingSession.objects.filter(departure__gte=now, scheduled=True)
    if future_sessions:
        assert len(future_sessions) == 1, "Somehow, there are 2 sessions planned!?"
        return redirect('/charge/session/{}'.format(future_sessions[0].pk))

    departure_hour = int(request.GET.get("departure_hour", 8 if datetime.now().hour < 8 else 17))
    hours_needed = float(request.GET.get("hours_needed", 2))
    max_cost = int(request.GET.get("max_cost", 15))

    now = datetime.now(tz=get_localzone())
    ep_pd = energy_planner.ep_df_from_now()

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
        start = SystemScheduleTasks(action_time=period.start_time,
                                    function=tesla_start_charging.__name__)
        start.save()
        period.start_task_id = start

        end = SystemScheduleTasks(action_time=period.stop_time,
                                  function=tesla_stop_charging.__name__)
        end.save()
        period.stop_task_id = end

    charge_session.scheduled = True
    charge_session.save()

    return redirect("/charge")


def show_charge(request, session_id):
    charge_session = CarChargingSession.objects.get(pk=session_id)

    starts_and_stops = [(s.start_time, s.stop_time) for s in charge_session.carchargingperiod_set.all()]

    start_time = min(starts_and_stops[0][0], start_of_current_period())

    ep_pd = energy_planner.ep_df_from_now(start_time=start_time)
    graph = plot_html([ep_pd], starts_and_stops=starts_and_stops, end_marker=charge_session.departure)

    return render(request, 'show_charge.html', context={"graph": graph,
                                                        "charge_session": charge_session})


def cancel_charge(request, session_id):
    CarChargingSession.objects.get(pk=session_id).delete()
    return redirect("/charge")
