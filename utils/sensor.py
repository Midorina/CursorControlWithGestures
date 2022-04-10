# https://github.com/mbientlab/MetaWear-SDK-Python

import logging
import time

from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import *

__all__ = ['Sensor']

from utils.cursor import CursorController


class Sensor(MetaWear):
    def __init__(self, address: str = "FA:49:1B:40:C1:DF", **kwargs) -> None:
        super(Sensor, self).__init__(address, **kwargs)

        self.acc_callback = FnVoid_VoidP_DataP(self.acc_data_handler)
        self.gyro_callback = FnVoid_VoidP_DataP(self.gyro_data_handler)

        self.cursor = CursorController()

    def acc_data_handler(self, ctx: None, data):
        data: CartesianFloat = parse_value(data)
        logging.debug("%s -> %s" % (self.address, data))

        x_pos = data.y * 1000
        y_pos = data.z * -1000
        self.cursor.move_in_x_axis(x_pos // 150)
        self.cursor.move_in_y_axis(y_pos // 150)

    def gyro_data_handler(self, ctx: None, data):
        data: CartesianFloat = parse_value(data)
        logging.debug("%s -> %s" % (self.address, data))

    def connect(self) -> None:
        attempts = 0
        while attempts < 10:
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

    def start_acc_capturing(self) -> None:
        self.__setup_acc()
        self.__start_acc()

    def start_gyro_capturing(self) -> None:
        self.__setup_gyro()
        self.__start_gyro()

    def stop_acc_capturing(self) -> None:
        # stop acc
        libmetawear.mbl_mw_acc_stop(self.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(self.board)

        # unsubscribe acc
        acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(acc_signal)

    def stop_gyro_capturing(self) -> None:
        # stop gyro
        libmetawear.mbl_mw_gyro_bmi160_stop(self.board)
        libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(self.board)

        # unsubscribe gyro
        gyro_signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(gyro_signal)

    def disconnect(self) -> None:
        libmetawear.mbl_mw_debug_disconnect(self.board)
        super().disconnect()

    def __setup_ble(self) -> None:
        libmetawear.mbl_mw_settings_set_connection_parameters(self.board, 7.5, 7.5, 0, 6000)
        # time.sleep(1.5)

    def __setup_acc(self) -> None:
        self.__setup_ble()

        # setup acc
        libmetawear.mbl_mw_acc_set_odr(self.board, 100.0)
        libmetawear.mbl_mw_acc_set_range(self.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(self.board)

        # get acc signal and subscribe
        acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.board)
        libmetawear.mbl_mw_datasignal_subscribe(acc_signal, None, self.acc_callback)

    def __setup_gyro(self) -> None:
        self.__setup_ble()

        # setup gyro
        libmetawear.mbl_mw_gyro_bmi160_set_range(self.board, GyroBoschRange._1000dps)
        libmetawear.mbl_mw_gyro_bmi160_set_odr(self.board, GyroBoschOdr._50Hz)
        libmetawear.mbl_mw_gyro_bmi160_write_config(self.board)

        # get gyro signal and subscribe
        gyro_signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.board)
        libmetawear.mbl_mw_datasignal_subscribe(gyro_signal, None, self.gyro_callback)

    def __start_acc(self) -> None:
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.board)
        libmetawear.mbl_mw_acc_start(self.board)

    def __start_gyro(self) -> None:
        libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.board)
        libmetawear.mbl_mw_gyro_bmi160_start(self.board)
