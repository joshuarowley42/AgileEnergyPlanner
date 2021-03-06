import logging
from config import *
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
        """
        This function gets electricity prices, but includes a little contextual knowledge about what data
        is likely to be available before just heading off to get it blindly.
        """
        now = datetime.now(tz=timezone.utc)

        # We will never have more data than this
        if start_time > now.replace(hour=21, minute=30,
                                    second=0, microsecond=0) + timedelta(days=1):
            logging.info(f"Data won't be available that far in the future ({start_time}).")
            return {}

        # Before 1600 (UK) - we know we won't have data for anything beyond 2200 (UTC) tonight.
        if now.astimezone(TIMEZONE).hour < 16 and start_time > now.replace(hour=21, minute=30,
                                                                           second=0, microsecond=0):
            logging.info(f"Data won't be available that far in the future ({start_time}).")
            return {}

        # At this point - it's worth hitting the API.

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
            logging.info(f"Octopus API request: {url}")
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

    def get_elec_usage(self, start_time, end_time=None):

        url = f"{self.base_url}/" \
              f"electricity-meter-points/{self.e_mpan}/" \
              f"meters/{self.e_msn}/" \
              f"consumption/"
        return self.get_usage(url, start_time, end_time)

    def get_gas_usage(self, start_time, end_time=None):
        url = f"{self.base_url}/" \
              f"gas-meter-points/{self.g_mprn}/" \
              f"meters/{self.g_msn}/" \
              f"consumption/"

        return self.get_usage(url, start_time, end_time)

    def get_usage(self, url, start_time, end_time=None):

        # We will never data in the future
        now = datetime.now(tz=timezone.utc)
        if start_time > now:
            logging.info(f"Data won't be available in the future ({start_time}).")
            return {}

        usage = []
        params = {"period_from": datetime.strftime(start_time, "%Y-%m-%dT%H:%M:%S%z")}
        if end_time is not None:
            params["period_to"] = datetime.strftime(end_time, "%Y-%m-%dT%H:%M:%S%z")

        while url is not None:
            logging.info(f"Octopus API request: {url}")
            r = requests.get(url, auth=self.auth, params=params)
            response = r.json()
            usage += response["results"]
            url = response.get("next", None)

        usage_dict = {}
        for i in usage:
            assert read_datetime(i["interval_end"]) - read_datetime(i["interval_start"]) == timedelta(
                minutes=30), "periods not equal to 30m not supported"
            usage_dict[read_datetime(i["interval_start"])] = i["consumption"]
        return usage_dict
