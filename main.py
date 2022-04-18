from datetime import datetime
from typing import Dict, List, Optional, Tuple

from controllers import CameraControllerDlib, SensorController
from models import Cursor, Eye

SENSOR_ADDRESS = "FA:49:1B:40:C1:DF"
SENSOR_DEADZONE = 45
SENSOR_SENSITIVITY = 7  # 1-1000 (the lower, the slower)
BLINK_THRESHOLD_MS = 50
BLINK_THRESHOLD_RATIO = 5.7


class MainController(object):
    def __init__(self) -> None:
        self.sensor: SensorController = SensorController(address=SENSOR_ADDRESS, acc_callback=self.sensor_data_handler)
        self.camera: CameraControllerDlib = CameraControllerDlib(eye_callback=self.camera_data_handler, blink_threshold=BLINK_THRESHOLD_RATIO)

        self.cursor: Cursor = Cursor(use_center_as_starting_point=True, allow_external_movement=True)

        # used to calibrate first position
        self.first_x: Optional[int] = None
        self.first_y: Optional[int] = None

        # used to get rid of false positives
        self.last_eye_states: Dict[Eye.Type, Dict[Eye.State, Tuple[bool, Optional[datetime]]]] = {
            Eye.Type.LEFT : {
                Eye.State.OPEN  : (False, None),
                Eye.State.CLOSED: (False, None)
            },
            Eye.Type.RIGHT: {
                Eye.State.OPEN  : (False, None),
                Eye.State.CLOSED: (False, None)
            },
        }

    def sensor_data_handler(self, x: float, y: float) -> None:
        # make them int
        x_pos = x * 1000
        y_pos = y * -1000  # invert y

        if self.first_x is None:
            self.first_x, self.first_y = x_pos, y_pos
        else:
            x_pos -= self.first_x
            y_pos -= self.first_y

        # dead-zone check
        x_pos = 0 if -SENSOR_DEADZONE < x_pos < SENSOR_DEADZONE else x_pos - SENSOR_DEADZONE
        y_pos = 0 if -SENSOR_DEADZONE < y_pos < SENSOR_DEADZONE else y_pos - SENSOR_DEADZONE

        self.cursor.move_in_x_axis(x_pos // (1000 // SENSOR_SENSITIVITY))
        self.cursor.move_in_y_axis(y_pos // (1000 // SENSOR_SENSITIVITY))

    # TODO: write another handler which uses both eyes blink as left click
    def camera_data_handler(self, eyes: List[Eye]) -> None:
        def blink_handler(eye: Eye) -> None:
            if eye.type == Eye.Type.LEFT:
                press_function = self.cursor.press_left_click
                release_function = self.cursor.release_left_click
            else:
                press_function = self.cursor.press_right_click
                release_function = self.cursor.release_right_click

            if eye.state == Eye.State.CLOSED:
                press_function()
            else:
                release_function()

        for eye in eyes:
            if eye.type == Eye.Type.UNKNOWN:
                continue  # only in Haar

            action_done, before = self.last_eye_states[eye.type][eye.state]
            now = datetime.now()

            # if we have never received this eye before, just set and continue
            if before is None:
                self.last_eye_states[eye.type][eye.state] = False, now
                continue

            # threshold check
            diff_in_ms = (now - before).total_seconds() * 1000
            if diff_in_ms >= BLINK_THRESHOLD_MS and not action_done:
                # update current state,
                self.last_eye_states[eye.type][eye.state] = True, before

                # reset other state
                self.last_eye_states[eye.type][eye.state.get_opposite()] = False, None

                # blink
                blink_handler(eye)


    def run(self):
        self.sensor.connect()
        self.sensor.start_acc_capturing()

        self.camera.start_capturing()

    def stop(self):
        self.camera.stop()

        self.sensor.stop_acc_capturing()
        self.sensor.disconnect()
