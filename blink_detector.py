import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils import Color, Eye, Face, Timer, draw_text

# initializing the face and eye cascade classifiers from xml files
FACE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
EYE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_eye_tree_eyeglasses.xml')


class BlinkDetector:
    def __init__(self):
        # our capture device
        self.capture_device = None
        # last captured frame
        self.img: Optional[np.ndarray] = None

        # last detected objects
        self.last_detected_face: Optional[Face] = None
        self.last_detected_left_eye: Optional[Eye] = None
        self.last_detected_right_eye: Optional[Eye] = None

        self.timer = Timer()

    @property
    def eye_cache(self) -> List[Eye]:
        return [x for x in (self.last_detected_left_eye, self.last_detected_right_eye) if x is not None]

    def refresh_video_frame(self) -> bool:
        """Refreshes the frame."""
        if not self.capture_device:
            self.capture_device = cv2.VideoCapture(0)

        success, self.img = self.capture_device.read()

        return success is True

    def _add_to_cache(self, eye: Eye):
        """Adds a captured eye to the cache depending on its type."""
        if not eye:
            return

        if eye.type is Eye.Type.LEFT:
            self.last_detected_left_eye = eye
        else:
            self.last_detected_right_eye = eye

    def parse_eye_coords_and_update_cache(
            self,
            face: Face,
            detected_eye_coords: List[Tuple[int, int, int, int]]) -> None:
        """Parses the captured eye coordinates and updates the cache."""
        if len(detected_eye_coords) >= 2:  # if we managed to detect both eyes, simple algo
            if detected_eye_coords[0][0] < detected_eye_coords[1][0]:
                left_eye = detected_eye_coords[0]
                right_eye = detected_eye_coords[1]
            else:
                right_eye = detected_eye_coords[0]
                left_eye = detected_eye_coords[1]

            self.last_detected_left_eye = Eye(
                face=face,
                base_image=self.img, eye_type=Eye.Type.LEFT,
                state=Eye.State.OPEN, coordinates=left_eye)
            self.last_detected_right_eye = Eye(
                face=face,
                base_image=self.img, eye_type=Eye.Type.RIGHT,
                state=Eye.State.OPEN, coordinates=right_eye)

        else:  # if not, use the latest detected eyes
            coords = detected_eye_coords[0]
            eye_type = Eye.Type.UNKNOWN
            other_eye: Optional[Eye] = None

            # if we dont have any previously detected eyes, return unknown
            if not self.last_detected_right_eye and not self.last_detected_left_eye:
                eye_type = Eye.Type.UNKNOWN

            else:
                for cached_eye in self.eye_cache:
                    # if the X coord difference is less than 20 pixels to the cached eye,
                    # its probably the same eye type as cached eye
                    x_diff = abs(coords[0] - cached_eye.coordinates[0])
                    if x_diff < 20:
                        eye_type = cached_eye.type

                # assign and update the other eye
                if eye_type is not Eye.Type.UNKNOWN:
                    other_eye = self.last_detected_right_eye if eye_type is Eye.Type.LEFT else self.last_detected_left_eye
                    other_eye.state = Eye.State.CLOSED

            eye = Eye(base_image=self.img, eye_type=eye_type, state=Eye.State.OPEN, coordinates=coords)

            self._add_to_cache(eye)
            self._add_to_cache(other_eye)

    def start(self):
        """Main loop."""
        successful = self.refresh_video_frame()

        if not successful:
            logging.error("Camera not found. Exiting.")
            exit()

        frame_counter = 0
        while successful:
            frame_counter += 1

            # capturing frame is kept out of time frame
            # because it is inconsistent and takes too much time compared to others
            successful = self.refresh_video_frame()
            # _capturing_frame_time = perf_counter() - _base_time
            # processing_times["capturing_frame"][frame_counter] = _capturing_frame_time

            self.timer.start()
            # filtering
            # flip the image (this might vary on camera device)
            self.img = cv2.flip(
                self.img,
                1  # 0 = flip around x, 1 = flip around y, -1 = both
            )

            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # convert to grayscale
            gray = cv2.bilateralFilter(gray, 5, 1, 1)  # remove impurities

            self.timer.capture("filtering", frame_counter)

            # detecting faces
            self.timer.start()
            faces: Optional[List[Face]] = [
                Face(self.img, coord)
                for coord in FACE_CASCADE.detectMultiScale(
                    gray,
                    scaleFactor=1.3,  # the higher, the faster but less accurate
                    minNeighbors=5,  # the higher, the less false positives but higher chance of missing
                    minSize=(200, 200)
                )
            ]
            self.timer.capture("face_detection", frame_counter)

            if len(faces) <= 0:
                draw_text(
                    self.img,
                    text="No face detected",
                    coords=(100, 100),
                    color=Color.RED)

            else:
                for face in faces:
                    # labels
                    face.draw_name(self.img)
                    face.draw_rectangle(self.img)

                    # crop the filtered image using detected face's region
                    face_region = gray[face.y:face.y + face.height, face.x:face.x + face.width]

                    self.timer.start()

                    # detect eye coordinates
                    detected_eyes = EYE_CASCADE.detectMultiScale(face_region, 1.3, 5, minSize=(50, 50))
                    self.timer.capture("eye_detection", frame_counter)

                    # if we couldn't detect any new eye
                    if len(detected_eyes) <= 0:
                        if len(self.eye_cache) <= 0:  # if the cache is empty
                            draw_text(self.img, "No eyes detected", color=Color.RED)
                        else:
                            # update the status of eyes in the cache
                            for eye in self.eye_cache:
                                eye.state = Eye.State.CLOSED
                    else:
                        # parse new detected eyes
                        self.parse_eye_coords_and_update_cache(face, detected_eyes)

                    # labels
                    for eye in self.eye_cache:
                        eye.draw_name(self.img, face=face)
                        eye.draw_rectangle(self.img, face=face)

            # show the image
            cv2.imshow('img', self.img)

            self.timer.capture("total", frame_counter, use_beginning=True)

            # if the user presses q, break
            if cv2.waitKey(1) == ord('q'):
                break

        self.capture_device.release()
        cv2.destroyAllWindows()
        self.timer.show_graph()
