from django.contrib import admin
from .models import CarChargingPeriod, CarChargingSession


class CarChargingPeriodAdmin(admin.ModelAdmin):
    pass


class CarChargingSessionAdmin(admin.ModelAdmin):
    pass


admin.site.register(CarChargingPeriod, CarChargingPeriodAdmin)
admin.site.register(CarChargingSession, CarChargingSessionAdmin)

