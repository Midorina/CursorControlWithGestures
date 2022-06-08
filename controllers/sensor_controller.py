# https://github.com/mbientlab/MetaWear-SDK-Python

import logging
from typing import Callable

from mbientlab.metawear import libmetawear, parse_value
from mbientlab.metawear.cbindings import *

from models.sensor import Sensor

__all__ = ['SensorController']


class SensorController(object):
    def __init__(self, address: str, acc_callback: Callable = None, gyro_callback: Callable = None) -> None:
        self.sensor = Sensor(address)

        # callbacks
        self.acc_callback = acc_callback
        self.gyro_callback = gyro_callback

        # preprocessors
        self._acc_preprocessor = FnVoid_VoidP_DataP(self.acc_preprocessor)
        self._gyro_preprocessor = FnVoid_VoidP_DataP(self.gyro_preprocessor)

    def acc_preprocessor(self, ctx: None, data) -> None:
        data: CartesianFloat = parse_value(data)
        logging.info(f"{self.sensor.address} -> {data}")

        if self.acc_callback:
            self.acc_callback(data.y, data.z)

    def gyro_preprocessor(self, ctx: None, data) -> None:
        data: CartesianFloat = parse_value(data)
        logging.debug(f"{self.sensor.address} -> {data}")

        if self.gyro_callback:
            self.gyro_callback(data.y, data.z)

    def connect(self) -> None:
        self.sensor.connect()

    def start_acc_capturing(self) -> None:
        self.__setup_acc()
        self.__start_acc()

    def start_gyro_capturing(self) -> None:
        self.__setup_gyro()
        self.__start_gyro()

    def stop_acc_capturing(self) -> None:
        # stop acc
        libmetawear.mbl_mw_acc_stop(self.sensor.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(self.sensor.board)

        # unsubscribe acc
        acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.sensor.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(acc_signal)

    def stop_gyro_capturing(self) -> None:
        # stop gyro
        libmetawear.mbl_mw_gyro_bmi160_stop(self.sensor.board)
        libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(self.sensor.board)

        # unsubscribe gyro
        gyro_signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.sensor.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(gyro_signal)

    def disconnect(self) -> None:
        libmetawear.mbl_mw_debug_disconnect(self.sensor.board)
        self.sensor.disconnect()

    def __setup_ble(self) -> None:
        libmetawear.mbl_mw_settings_set_connection_parameters(self.sensor.board, 7.5, 7.5, 0, 6000)
        # time.sleep(1.5)

    def __setup_acc(self) -> None:
        self.__setup_ble()

        # setup acc
        libmetawear.mbl_mw_acc_set_odr(self.sensor.board, 100.0)
        libmetawear.mbl_mw_acc_set_range(self.sensor.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(self.sensor.board)

        # get acc signal and subscribe
        acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.sensor.board)
        libmetawear.mbl_mw_datasignal_subscribe(acc_signal, None, self._acc_preprocessor)

    def __setup_gyro(self) -> None:
        self.__setup_ble()

        # setup gyro
        libmetawear.mbl_mw_gyro_bmi160_set_range(self.sensor.board, GyroBoschRange._1000dps)
        libmetawear.mbl_mw_gyro_bmi160_set_odr(self.sensor.board, GyroBoschOdr._50Hz)
        libmetawear.mbl_mw_gyro_bmi160_write_config(self.sensor.board)

        # get gyro signal and subscribe
        gyro_signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.sensor.board)
        libmetawear.mbl_mw_datasignal_subscribe(gyro_signal, None, self._gyro_preprocessor)

    def __start_acc(self) -> None:
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.sensor.board)
        libmetawear.mbl_mw_acc_start(self.sensor.board)

    def __start_gyro(self) -> None:
        libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.sensor.board)
        libmetawear.mbl_mw_gyro_bmi160_start(self.sensor.board)
