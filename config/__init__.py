# WARNING - Don't put any confidential information in here if you plan to
# version-control your instance of this bodebase. Instead; create a file
# "local_config.py" in this directory and declare any variables you don't
# want in version control in there.


from datetime import time
import pytz

TIMEZONE = pytz.timezone("Europe/London")

DEV_MODE = False

PHASE_A_END = time(hour=8)
PHASE_B_END = time(hour=23)

OCTOPUS_USERNAME = "sk_live_xxx"
OCTOPUS_ZONE = "H"                  # H = Southern England
OCTOPUS_ELEC_MPAN = ""
OCTOPUS_ELEC_MSN = ""
OCTOPUS_GAS_MPRN = ""
OCTOPUS_GAS_MSN = ""

TESLA_USERNAME = ""
TESLA_PASSWORD = ""

TEXTLOCAL_USERNAME = ""
TEXTLOCAL_API_HASH = ""
TEXTLOCAL_API_KEY = ""
TEXTLOCAL_SENDER = "AgilePlanner"

SMS_PHONE_NUMERS = ['447xxxxxxx']

EMAIL_SENDER = ""
EMAIL_RECIPIENTS = []
SENDGRID_API_KEY = ""


try:
    from .local_config import *
except ImportError:
    pass
