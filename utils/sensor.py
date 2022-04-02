# https://github.com/mbientlab/MetaWear-SDK-Python

import logging
import time

from mbientlab.metawear import MetaWear
from mbientlab.warble import WarbleException

# temporary logging config
logging.basicConfig(level=logging.INFO)


class Sensor(object):
    def __init__(self, address: str = "FA:49:1B:40:C1:DF") -> None:
        self.device: MetaWear = MetaWear(address)

    def connect(self) -> None:
        attempts = 0
        while attempts < 5:
            try:
                self.device.connect()

            except WarbleException:
                logging.warning("Sensor connection could not be established. This is normal on Windows. Re-trying...")
                attempts += 1
                time.sleep(0.5)

            else:
                return logging.info("Sensor connection successful.")

        logging.error("Could not establish connection with the sensor.")


a = Sensor()
a.connect()
