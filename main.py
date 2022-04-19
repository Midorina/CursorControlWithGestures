from datetime import datetime
from typing import Dict, List, Optional, Tuple

from controllers import CameraControllerDlib, SensorController
from models import Cursor, Eye

SENSOR_ADDRESS = "FA:49:1B:40:C1:DF"
SENSOR_DEADZONE = 60
SENSOR_SENSITIVITY = 7.5  # 1-1000 (the lower, the slower)
BLINK_SHORT_THRESHOLD_MS = 100  # average blink duration is between 100 and 400 ms
BLINK_LONG_THRESHOLD_MS = 350
BLINK_DETECTION_RATIO = 5.7


class MainController(object):
    def __init__(self) -> None:
        self.sensor: SensorController = SensorController(address=SENSOR_ADDRESS, acc_callback=self.sensor_data_handler)
        self.camera: CameraControllerDlib = CameraControllerDlib(eye_callback=self.double_blink_algorithm,
                                                                 blink_threshold=BLINK_DETECTION_RATIO)

        self.cursor: Cursor = Cursor(use_center_as_starting_point=True, allow_external_movement=True)

        # used to calibrate first position
        self.first_x: Optional[int] = None
        self.first_y: Optional[int] = None

        # used to get rid of false positives
        self.individual_eye_cache: Dict[Eye.Type, Dict[Eye.State, Tuple[bool, Optional[datetime]]]] = {
            Eye.Type.LEFT : {
                Eye.State.OPEN  : (False, None),
                Eye.State.CLOSED: (False, None)
            },
            Eye.Type.RIGHT: {
                Eye.State.OPEN  : (False, None),
                Eye.State.CLOSED: (False, None)
            },
        }

        self.both_eye_last_state: Optional[Tuple[Eye.State, datetime, bool]] = None

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

    def single_eye_blink_algorithm(self, left_eye: Eye, right_eye: Eye) -> None:
        def blink_handler(_eye: Eye) -> None:
            if _eye.type == Eye.Type.LEFT:
                press_function = self.cursor.press_left_click
                release_function = self.cursor.release_left_click
            else:
                press_function = self.cursor.press_right_click
                release_function = self.cursor.release_right_click

            if _eye.state == Eye.State.CLOSED:
                press_function()
            else:
                release_function()

        for eye in [left_eye, right_eye]:
            if eye.type == Eye.Type.UNKNOWN:
                continue  # only in Haar

            action_done, before = self.individual_eye_cache[eye.type][eye.state]
            now = datetime.now()

            # if we have never received this eye before, just set and continue
            if before is None:
                self.individual_eye_cache[eye.type][eye.state] = False, now
                continue

            # threshold check
            diff_in_ms = (now - before).total_seconds() * 1000
            if diff_in_ms >= BLINK_SHORT_THRESHOLD_MS and not action_done:
                # update current state,
                self.individual_eye_cache[eye.type][eye.state] = True, before

                # reset other state
                self.individual_eye_cache[eye.type][eye.state.get_opposite()] = False, None

                # blink
                blink_handler(eye)

    def double_blink_algorithm(self,  left_eye: Eye, right_eye: Eye) -> None:
        now = datetime.now()

        # threshold check
        ratio = (left_eye.closeness_ratio + right_eye.closeness_ratio) / 2
        current_state: Eye.State = Eye.State.CLOSED if ratio >= BLINK_DETECTION_RATIO else Eye.State.OPEN

        # if we have never received a state before, just set and return
        if self.both_eye_last_state is None:
            self.both_eye_last_state = current_state, now, False
            return

        before_state, last_state_time, action_taken = self.both_eye_last_state
        diff_in_ms = (now - last_state_time).total_seconds() * 1000

        if before_state != current_state:  # if this is a different state than the last one
            self.both_eye_last_state = current_state, now, False

            if before_state == Eye.State.CLOSED:  # and if eyes just got opened
                if diff_in_ms > BLINK_SHORT_THRESHOLD_MS and not action_taken:
                    # and if it was closed for long enough and action not taken, left click
                    return self.cursor.left_click()

        else:  # if same, either eye is just open, or closed for too long.
            if current_state == Eye.State.CLOSED and diff_in_ms > BLINK_LONG_THRESHOLD_MS and not action_taken:
                # if closed for too long, right click and return
                self.both_eye_last_state = current_state, last_state_time, True
                return self.cursor.right_click()

    def run(self):
        self.sensor.connect()
        self.sensor.start_acc_capturing()

        self.camera.start_capturing()

    def stop(self):
        self.camera.stop()

        self.sensor.stop_acc_capturing()
        self.sensor.disconnect()
