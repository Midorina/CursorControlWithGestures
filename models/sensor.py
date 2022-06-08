# https://github.com/mbientlab/MetaWear-SDK-Python

import logging
import time

from mbientlab.metawear import MetaWear
from mbientlab.warble import *

__all__ = ['Sensor']


class Sensor(MetaWear):
    def __init__(self, address: str, **kwargs) -> None:
        super(Sensor, self).__init__(address, **kwargs)

    def connect(self) -> None:
        attempts = 0
        while attempts < 1000:
            try:
                super(Sensor, self).connect()

            except WarbleException as e:
                logging.warning("Sensor connection could not be established. This is normal on Windows. Re-trying...")
                logging.error(e)
                attempts += 1
                time.sleep(0.5)

            else:
                return logging.info("Sensor connection successful.")

        logging.error("Could not establish connection with the sensor.")
