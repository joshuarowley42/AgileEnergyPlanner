import teslapy
import logging


class TeslaAPIClient:
    def __init__(self, email, password, dry_run=True):
        self.tesla = teslapy.Tesla(email=email,
                                   password=password)
        self.tesla.fetch_token()
        vehicles = self.tesla.vehicle_list()
        assert len(vehicles) == 1, "Can only handle one car!"
        self.tesla = vehicles[0]

        if dry_run:
            logging.warning("Tesla created in dry_run mode. Won't do much!")

        self.dry_run = dry_run

    @property
    def vehicle_data(self):
        self.tesla.sync_wake_up()
        return self.tesla.get_vehicle_data()

    @property
    def hours_to_target_soc(self):
        charge = self.vehicle_data['charge_state']['battery_level']/100.0
        target = self.vehicle_data['charge_state']['charge_limit_soc_std']/100.0
        kw = self.vehicle_data['charge_state']['charge_current_request']*0.240      # Todo: Add phases
        charge_needed = (target - charge)*75
        return charge_needed / kw

    def start_charging(self):
        self.tesla.sync_wake_up()
        if self.dry_run:
            assert self.vehicle_data
            logging.info("START_CHARGE: Dry-run on. Got vehicle data. Seemed to work.")
            return
        self.tesla.command("START_CHARGE")

    def stop_charging(self):
        self.tesla.sync_wake_up()
        if self.dry_run:
            assert self.vehicle_data
            logging.info("STOP_CHARGE: Dry-run on. Got vehicle data. Seemed to work.")
            return
        self.tesla.command("STOP_CHARGE")
