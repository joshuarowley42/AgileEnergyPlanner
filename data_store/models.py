from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, DateTime, Float
from datetime import timezone

engine = create_engine('sqlite:///db.sqlite', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

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


Base.metadata.create_all(engine)


