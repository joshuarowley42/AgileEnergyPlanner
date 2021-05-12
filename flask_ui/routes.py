from flask_ui import app

from config import *
from octopus import OctopusClient
from datetime import datetime, timezone

energy_provider = OctopusClient(username=OCTOPUS_USERNAME,
                                zone=OCTOPUS_ZONE,
                                e_mpan=OCTOPUS_ELEC_MPAN,
                                e_msn=OCTOPUS_ELEC_MSN,
                                g_mprn=OCTOPUS_GAS_MPRN,
                                g_msn=OCTOPUS_GAS_MSN)


@app.route('/')
@app.route('/index')
def index():
    prices = energy_provider.get_elec_price(start_time=datetime(year=2021,
                                                                month=5,
                                                                day=9,
                                                                tzinfo=timezone.utc),
                                            end_time=datetime(year=2021,
                                                              month=5,
                                                              day=11,
                                                              hour=1,
                                                              tzinfo=timezone.utc))
    return {str(p): prices[p] for p in prices}
