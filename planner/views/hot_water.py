from django.shortcuts import redirect, render
from planner.common import energy_planner


def hot_water(request):
    energy_planner.plan_water_heating()

    return render(request, 'show_water.html', context={"graph": None,
                                                        "session_config": None,
                                                        "charge_session": None})
