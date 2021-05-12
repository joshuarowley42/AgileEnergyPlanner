from flask_ui import app

from config import *
from octopus import OctopusClient
from datetime import datetime, timezone, timedelta

energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)


@app.route('/')
def index():
    start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=20)
    prices = energy_provider.get_elec_price(start_time=start)
    return {str(p): prices[p] for p in prices}
