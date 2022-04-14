from typing import Optional

from controllers import SensorController, CameraController
from models import Cursor, Eye

SENSOR_ADDRESS = "FA:49:1B:40:C1:DF"
SENSOR_DEADZONE = 75
SENSOR_SENSITIVITY = 15  # 1-1000 (the lower, the faster)


class MainController(object):
    def __init__(self):
        self.sensor = SensorController(address=SENSOR_ADDRESS, acc_callback=self.sensor_data_handler)
        self.camera = CameraController(eye_callback=self.camera_data_handler)

        # TODO: use the center of the screen instead
        self.cursor = Cursor().get_with_current()

        # used to calibrate first position
        self.first_x = self.first_y = None

    def sensor_data_handler(self, x: float, y: float):
        # make them int
        x_pos = x * 1000
        y_pos = y * -1000  # invert y

        if self.first_x is None:
            self.first_x, self.first_y = x_pos, y_pos
        else:
            x_pos -= self.first_x
            y_pos -= self.first_y

        # dead-zone
        x_pos = 0 if -SENSOR_DEADZONE < x_pos < SENSOR_DEADZONE else x_pos
        y_pos = 0 if -SENSOR_DEADZONE < y_pos < SENSOR_DEADZONE else y_pos

        self.cursor.move_in_x_axis(x_pos // (1000 // SENSOR_SENSITIVITY))
        self.cursor.move_in_y_axis(y_pos // (1000 // SENSOR_SENSITIVITY))

    def camera_data_handler(self, left_eye: Optional[Eye], right_eye: Optional[Eye]):
        # TODO: advanced click logic
        # if left_eye.state == Eye.State.CLOSED:
        #     self.cursor.press_left_click()
        # else:
        #     self.cursor.release_left_click()
        #
        # if right_eye.state == Eye.State.CLOSED:
        #     self.cursor.press_right_click()
        # else:
        #     self.cursor.release_right_click()
        return

    def blink_handler(self):
        self.cursor.left_click()

    def run(self):
        self.sensor.connect()
        self.sensor.start_acc_capturing()

        self.camera.start_capturing()

    def stop(self):
        self.camera.stop()

        self.sensor.stop_acc_capturing()
        self.sensor.disconnect()
