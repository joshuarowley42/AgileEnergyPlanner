from django.urls import path

import planner.views.shared
import planner.views.car_charging
import planner.views.hot_water

urlpatterns = [
    path('', planner.views.shared.index, name='index'),
    path('charge', planner.views.car_charging.plan_charge, name='charge'),
    path('charge/session/<int:session_id>', planner.views.car_charging.show_charge),
    path('charge/schedule/<int:session_id>', planner.views.car_charging.schedule_charge),
    path('charge/cancel/<int:session_id>', planner.views.car_charging.cancel_charge),
    path('water/', planner.views.hot_water.hot_water),
]