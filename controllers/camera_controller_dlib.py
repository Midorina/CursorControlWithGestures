import logging
from typing import Callable, Dict, List, Optional, Tuple

import _dlib_pybind11
import cv2
import numpy as np
import dlib

from models import Eye, Face
from utils import Color, Timer, draw_text

FACE_DETECTOR = dlib.get_frontal_face_detector()
SHAPE_PREDICTOR = dlib.shape_predictor("./assets/shape_predictor_68_face_landmarks.dat")
LEFT_EYE_LANDMARKS = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_LANDMARKS = [42, 43, 44, 45, 46, 47]

__all__ = ['CameraControllerDlib']


class CameraControllerDlib:
    def __init__(self, eye_callback: Callable = None, blink_threshold: float = 5.65):
        # callback
        self.callback = eye_callback
        # blink threshold
        self.blink_threshold = blink_threshold

        # our capture device and the last captured frame
        self.capture_device = None
        self.img: Optional[np.ndarray] = None

        # timer to show graph
        self.frame_counter = 0
        self.timer = Timer()

    def _successfully_refreshed_frame(self) -> bool:
        """Refreshes the frame."""
        if not self.capture_device:
            self.capture_device = cv2.VideoCapture(0)
            # self.capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            # self.capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not self.capture_device.isOpened():
            logging.error("Camera could not be found/opened. Exiting.")
            self.stop()

        successful, self.img = self.capture_device.read()

        if not successful:
            logging.error("Could not capture any frame. Exiting.")
            self.stop()

        self.frame_counter += 1

        return True

    def start_capturing(self):
        """Main loop."""
        while self._successfully_refreshed_frame():
            # capturing frame is kept out of time frame
            # because it is inconsistent and takes too much time compared to others
            # _capturing_frame_time = perf_counter() - _base_time
            # processing_times["capturing_frame"][frame_counter] = _capturing_frame_time

            # filtering
            self.timer.start(set_beginning=True)

            # flip the image (this might vary on camera device)
            self.img = cv2.flip(
                self.img,
                1  # 0 = flip around x, 1 = flip around y, -1 = both
            )

            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # convert to grayscale
            gray = cv2.bilateralFilter(gray, 5, 1, 1)  # remove impurities

            self.timer.capture("filtering", self.frame_counter)

            # face detection
            self.timer.start()
            faces: Optional[List[Face]] = [
                Face.get_from_dlib_rectangle(self.img, coord)
                for coord in
                FACE_DETECTOR.run(image=gray, upsample_num_times=0, adjust_threshold=0.0)[0]
            ]
            self.timer.capture("face_detection", self.frame_counter)

            if len(faces) <= 0:
                draw_text(
                    self.img,
                    text="No face detected",
                    color=Color.RED)
            else:
                # use the first detected face
                face = faces[0]

                # detect face landmarks
                self.timer.start()
                face_landmarks: _dlib_pybind11.full_object_detection = SHAPE_PREDICTOR(gray, face.get_dlib_rectangle())
                self.timer.capture("landmark_detection", self.frame_counter)

                # create eye objects
                left_eye = Eye.get_from_dlib_landmarks(self.img, face, Eye.Type.LEFT, LEFT_EYE_LANDMARKS,
                                                       face_landmarks, state_threshold=self.blink_threshold)
                right_eye = Eye.get_from_dlib_landmarks(self.img, face, Eye.Type.RIGHT, RIGHT_EYE_LANDMARKS,
                                                        face_landmarks, state_threshold=self.blink_threshold)
                # labels
                face.draw()
                left_eye.draw()
                right_eye.draw()

                # callback
                if self.callback:
                    self.callback(left_eye, right_eye)

            self.timer.capture("total", self.frame_counter, use_beginning=True)

            # show the image
            cv2.imshow('img', self.img)

            # if the user presses q, break
            if cv2.waitKey(1) == ord('q'):
                break

        self.stop()

    def stop(self):
        cv2.destroyAllWindows()
        self.capture_device.release()
        self.timer.show_graph()
