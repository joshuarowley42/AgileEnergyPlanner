from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import EnergyPrices, EmailLog, CarChargingSession, CarChargingPeriod, Base

engine = create_engine('sqlite:///db.sqlite')
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)
