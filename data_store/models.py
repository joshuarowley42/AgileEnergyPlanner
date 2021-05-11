from sqlalchemy.orm import declarative_base, validates, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, DateTime, Float, Boolean, ForeignKey
from datetime import timezone

Base = declarative_base()


class EnergyPrices(Base):
    __tablename__ = 'energy_prices'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime)
    price = Column(Float)

    @hybrid_property
    def time_utc(self):
        return self.time.replace(tzinfo=timezone.utc)

    @validates('time')
    def validate_email(self, key, time):
        assert time.tzinfo == timezone.utc, "All times must be UTC going into the database"
        return time

    def __repr__(self):
        return "<Price(time={}, price={})>".format(self.time, self.price)


class EmailLog(Base):
    __tablename__ = 'email_log'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime)

    @hybrid_property
    def time_utc(self):
        return self.time.replace(tzinfo=timezone.utc)

    def __repr__(self):
        return "<Price(time={}, price={})>".format(self.time, self.price)


class CarChargingSession(Base):
    __tablename__ = 'car_charging_session'

    id = Column(Integer, primary_key=True)
    departure = Column(DateTime)

    children = relationship("CarChargingPeriod",
                            cascade="all, delete, delete-orphan")


class CarChargingPeriod(Base):
    __tablename__ = 'car_charging_period'

    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    scheduled = Column(Boolean)

    parent_id = Column(Integer, ForeignKey('car_charging_session.id'))
