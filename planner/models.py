from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from tzlocal import get_localzone
import pytz


def check_timezone(time):
    if not time.tzinfo:
        raise ValidationError("All times must have timezone going into the database")


class EnergyPrices(models.Model):
    __tablename__ = 'energy_prices'

    time = models.DateTimeField(unique=True, validators=[check_timezone])
    price = models.FloatField()

    def __repr__(self):
        return f"<Price(time={self.time}, price={self.price})>"


class EmailLog(models.Model):
    __tablename__ = 'email_log'

    time = models.DateTimeField(validators=[check_timezone])

    def __repr__(self):
        return f"<Price(time={self.time})>"


class SystemStatus(models.Model):

    system_id = models.IntegerField(unique=True)

    hw_nest_override = models.BooleanField()        # Are we disabling the Nest to take control ourselves?
    hw_elec_heater_on = models.BooleanField()       # Electric heater status
    hw_gas_heater_on = models.BooleanField()        # Gas..

    ev_charge_override = models.BooleanField()      # If car state not reflecting `ev_charging`; will we update car?
    ev_charging = models.BooleanField()             # Should we be charging now?
    ev_soc = models.IntegerField()                  # Latest SoC
    ev_last_updated = models.DateTimeField(         # When did we last get info from the API
        validators=[check_timezone])


class CarChargingSession(models.Model):
    __tablename__ = 'car_charging_session'

    departure = models.DateTimeField(validators=[check_timezone])
    average_cost = models.FloatField()
    scheduled = models.BooleanField()

    def as_dict(self):
        return {"id": self.id,
                "departure": self.departure.replace(tzinfo=pytz.timezone("UTC"))}

    @property
    def departure_formatted(self) -> str:
        return datetime.strftime(self.departure.astimezone(get_localzone()), "%a %d %H%M")

    @property
    def children(self):
        return self.carchargingperiod_set.all()


class CarChargingPeriod(models.Model):
    __tablename__ = 'car_charging_period'

    start_time = models.DateTimeField(validators=[check_timezone])
    stop_time = models.DateTimeField(validators=[check_timezone])
    start_task_id = models.TextField()
    stop_task_id = models.TextField()

    parent = models.ForeignKey(CarChargingSession, on_delete=models.CASCADE)

    def as_dict(self):
        return {"id": self.id,
                "start_time": self.start_time.replace(tzinfo=pytz.timezone("UTC")),
                "stop_time": self.stop_time.replace(tzinfo=pytz.timezone("UTC")),
                "parent": self.parent_id}

    @property
    def start_time_formatted(self):
        return datetime.strftime(self.start_time.astimezone(get_localzone()), "%a %d %H%M")

    @property
    def stop_time_formatted(self):
        return datetime.strftime(self.stop_time.astimezone(get_localzone()), "%a %d %H%M")


class WaterHeatingPeriod(models.Model):
    __tablename__ = 'water_heating_period'

    elec_heating = models.BooleanField()
    start_time = models.DateTimeField(validators=[check_timezone])
    stop_time = models.DateTimeField(validators=[check_timezone])
    start_task_id = models.TextField()
    stop_task_id = models.TextField()

    def as_dict(self):
        return {"id": self.id,
                "start_time": self.start_time.replace(tzinfo=pytz.timezone("UTC")),
                "stop_time": self.stop_time.replace(tzinfo=pytz.timezone("UTC")),
                "elec_heating": self.elec_heating,
                }

    @property
    def start_time_formatted(self):
        return datetime.strftime(self.start_time.astimezone(get_localzone()), "%a %d %H%M")

    @property
    def stop_time_formatted(self):
        return datetime.strftime(self.stop_time.astimezone(get_localzone()), "%a %d %H%M")