from django.contrib import admin
from .models import CarChargingPeriod, CarChargingSession, SystemStatus


class CarChargingPeriodAdmin(admin.ModelAdmin):
    pass


class CarChargingSessionAdmin(admin.ModelAdmin):
    pass


class SystemStatusAdmin(admin.ModelAdmin):
    pass


admin.site.register(CarChargingPeriod, CarChargingPeriodAdmin)
admin.site.register(CarChargingSession, CarChargingSessionAdmin)
admin.site.register(SystemStatus, SystemStatusAdmin)

