from typing import List, Optional, Tuple

import cv2
import numpy as np

import drawing
from models import Eye, Face

# Initializing the face and eye cascade classifiers from xml files
FACE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
EYE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_eye_tree_eyeglasses.xml')


class BlinkDetector:
    def __init__(self):
        self.capture_device = None

        self.img: Optional[np.ndarray] = None

        self.last_detected_face: Optional[Face] = None

        self.last_detected_left_eye: Optional[Eye] = None
        self.last_detected_right_eye: Optional[Eye] = None

    @property
    def eye_cache(self) -> List[Eye]:
        return [x for x in (self.last_detected_left_eye, self.last_detected_right_eye) if x is not None]

    def refresh_video_frame(self) -> bool:
        if not self.capture_device:
            self.capture_device = cv2.VideoCapture(0)

        success, self.img = self.capture_device.read()

        return success is True

    def _add_to_cache(self, eye: Eye):
        if eye.type is Eye.Type.LEFT:
            self.last_detected_left_eye = eye
        else:
            self.last_detected_right_eye = eye

    def parse_eye_coords_and_update_cache(self, detected_eye_coords: List[Tuple[int, int, int, int]]) -> None:
        if len(detected_eye_coords) >= 2:  # if we managed to detect both eyes, simple algo
            if detected_eye_coords[0][0] < detected_eye_coords[1][0]:
                left_eye = detected_eye_coords[0]
                right_eye = detected_eye_coords[1]
            else:
                right_eye = detected_eye_coords[0]
                left_eye = detected_eye_coords[1]

            self.last_detected_left_eye = Eye(
                base_image=self.img, type=Eye.Type.LEFT,
                state=Eye.State.OPEN, coords=left_eye)
            self.last_detected_right_eye = Eye(
                base_image=self.img, type=Eye.Type.RIGHT,
                state=Eye.State.OPEN, coords=right_eye)

        else:  # if not, use the latest detected eyes
            coords = detected_eye_coords[0]
            eye_type = Eye.Type.UNKNOWN
            other_eye: Optional[Eye] = None

            # if we dont have any previously detected eyes, return unknown
            if not self.last_detected_right_eye and not self.last_detected_left_eye:
                eye_type = Eye.Type.UNKNOWN

            else:
                for cached_eye in self.eye_cache:
                    # if the X coord difference is less than 15 pixels to the cached eye,
                    # its probably the same eye type as cached eye
                    x_diff = abs(coords[0] - self.last_detected_left_eye.coords[0])
                    if x_diff < 20:
                        eye_type = cached_eye.type

                # assign other eye
                if eye_type is not Eye.Type.UNKNOWN:
                    other_eye = self.last_detected_right_eye if eye_type is Eye.Type.RIGHT else self.last_detected_left_eye
                    other_eye.state = Eye.State.CLOSED

            eye = Eye(base_image=self.img, type=eye_type, state=Eye.State.OPEN, coords=coords)

            self._add_to_cache(eye)

    def start(self):
        success = self.refresh_video_frame()

        while success:
            success = self.refresh_video_frame()

            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # convert to grayscale
            gray = cv2.bilateralFilter(gray, 5, 1, 1)  # remove impurities

            # detect faces
            faces: Optional[List[Face]] = [
                Face(self.img, coord)
                for coord in FACE_CASCADE.detectMultiScale(gray, 1.3, 5, minSize=(200, 200))
            ]

            if len(faces) <= 0:
                drawing.draw_text(
                    self.img,
                    text="No face detected",
                    coords=(100, 100),
                    color=drawing.Color.RED)

            else:
                for face in faces:
                    # labels
                    face.draw_name(self.img)
                    face.draw_rectangle(self.img)

                    # crop the filtered image using detected face's region
                    face_region = gray[face.y:face.y + face.height, face.x:face.x + face.width]

                    # detect eye coordinates
                    detected_eyes = EYE_CASCADE.detectMultiScale(face_region, 1.3, 5, minSize=(50, 50))

                    # if we couldn't detect any new eye
                    if len(detected_eyes) <= 0:
                        if len(self.eye_cache) <= 0:
                            drawing.draw_text(self.img, "No eyes detected", color=drawing.Color.RED)
                        else:
                            for eye in self.eye_cache:
                                eye.state = Eye.State.CLOSED
                    else:
                        # parse eyes
                        self.parse_eye_coords_and_update_cache(detected_eyes)

                    for eye in self.eye_cache:
                        eye.draw_name(self.img, face=face)
                        eye.draw_rectangle(self.img, face=face)

            cv2.imshow('img', self.img)

            if cv2.waitKey(1) == ord('q'):
                break

        self.capture_device.release()
        cv2.destroyAllWindows()


a = BlinkDetector()
a.start()
