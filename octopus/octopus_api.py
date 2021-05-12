
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone
import pytz


def read_datetime(date_str):
    d = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
    if d.tzinfo is None:
        d = pytz.timezone("UTC").localize(d)
    return d


class OctopusAPIClient:
    def __init__(self, username, zone,
                 e_mpan, e_msn,
                 g_mprn, g_msn):
        # https://octopus.energy/dashboard/developer/
        self.USERNAME = username
        self.PASSWORD = ""          # This is not a mistake. Username is secret.
        self.OCTOPUS_ZONE = zone

        self.GAS_PRICE = 3.0135

        self.base_url = "https://api.octopus.energy/v1"
        self.e_mpan = e_mpan
        self.e_msn = e_msn
        self.g_mprn = g_mprn
        self.g_msn = g_msn

        self.auth = HTTPBasicAuth(self.USERNAME, self.PASSWORD)

    def get_gas_price(self, start_time):
        # Generates a flat-line based on a fixed cost until 2200 tomorrow.

        now = datetime.now(tz=timezone.utc)
        end = datetime(year=now.year,
                       month=now.month,
                       day=now.day,
                       hour=22,
                       tzinfo=timezone.utc) + timedelta(days=1)

        periods = int((end - start_time)/timedelta(minutes=30))

        price_list = {}
        for i in range(periods):
            d = start_time + timedelta(minutes=30) * i
            price_list[d] = self.GAS_PRICE

        return price_list

    def get_elec_price(self, start_time, end_time=None):
        url = "{base}/products/" \
              "{tc}/electricity-tariffs/" \
              "E-1R-{tc}-{zone}/" \
              "standard-unit-rates".format(base=self.base_url,
                                           tc="AGILE-18-02-21",
                                           zone=self.OCTOPUS_ZONE)

        prices = []
        params = {"period_from": datetime.strftime(start_time, "%Y-%m-%dT%H:%M:%S%z")}
        if end_time is not None:
            params["period_to"] = datetime.strftime(end_time, "%Y-%m-%dT%H:%M:%S%z")

        while url is not None:
            r = requests.get(url, params=params)
            response = r.json()
            prices += response.get('results', [])
            url = response.get("next", None)

        price_list = {}
        for i in prices:
            assert read_datetime(i["valid_to"]) - read_datetime(i["valid_from"]) == timedelta(
                minutes=30), "periods not equal to 30m not supported"
            price_list[read_datetime(i["valid_from"])] = i["value_inc_vat"]

        return price_list

    def get_elec_usage(self, start_time):
        url = f"{self.base_url}/" \
              f"electricity-meter-points/{self.e_mpan}/" \
              f"meters/{self.e_msn}/" \
              f"consumption/"
        return self.get_usage(start_time, url)

    def get_gas_usage(self, start_time):
        url = f"{self.base_url}/" \
              f"gas-meter-points/{self.g_mprn}/" \
              f"meters/{self.g_msn}/" \
              f"consumption/"

        return self.get_usage(start_time, url)

    def get_usage(self, start_time, url):
        usage = []
        while url is not None:
            r = requests.get(url,
                             auth=self.auth,
                             params={
                                 "period_from": datetime.strftime(start_time, "%Y-%m-%dT%H:%M:%S%z")}
                             )
            response = r.json()
            usage += response["results"]
            url = response.get("next", None)

        usage_dict = {}
        for i in usage:
            assert read_datetime(i["interval_end"]) - read_datetime(i["interval_start"]) == timedelta(
                minutes=30), "periods not equal to 30m not supported"
            usage_dict[read_datetime(i["interval_start"])] = i["consumption"]
        return usage_dict
