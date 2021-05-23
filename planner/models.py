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

