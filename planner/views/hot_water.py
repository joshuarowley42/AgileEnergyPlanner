from django.shortcuts import redirect, render


def hot_water(request):
    # now = datetime.now(tz=get_localzone())
    #
    # future_sessions = CarChargingSession.objects.filter(departure__gte=now, scheduled=True)
    # if future_sessions:
    #     assert len(future_sessions) == 1, "Somehow, there are 2 sessions planned!?"
    #     return redirect('/charge/session/{}'.format(future_sessions[0].pk))
    #
    # departure_hour = int(request.GET.get("departure_hour", 8 if datetime.now().hour < 8 else 17))
    # hours_needed = float(request.GET.get("hours_needed", 2))
    # max_cost = int(request.GET.get("max_cost", 15))
    #
    # ep_pd = energy_planner.ep_df_from_now()
    #
    # graph = plot_html([ep_pd])
    #
    # session_config = {
    #     "departure_hour": departure_hour,
    #     "hours_needed": hours_needed,
    #     "max_cost": max_cost,
    # }

    return render(request, 'plan_charge.html', context={"graph": None,
                                                        "session_config": None,
                                                        "charge_session": None})
