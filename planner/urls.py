from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('charge', views.plan_charge, name='charge'),
    path('charge/session/<int:session_id>', views.show_charge),
    path('charge/schedule/<int:session_id>', views.schedule_charge),
    path('charge/cancel/<int:session_id>', views.cancel_charge),
]