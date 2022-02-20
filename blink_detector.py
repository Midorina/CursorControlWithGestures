import asyncio
import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils import Color, Eye, Face, Timer, draw_text, run_in_executor

# initializing the face and eye cascade classifiers from xml files
FACE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
EYE_CASCADE = cv2.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_eye_tree_eyeglasses.xml')


class BlinkDetector:
    def __init__(self):
        # our capture device
        self.capture_device = None
        self.frame_counter = 0
        # last captured frame
        self.img: Optional[np.ndarray] = None

        # last detected objects
        self.last_detected_face: Optional[Face] = None
        self.last_detected_left_eye: Optional[Eye] = None
        self.last_detected_right_eye: Optional[Eye] = None

        # timer to show graph
        self.timer = Timer()

        self.stopped = False

    @property
    def eye_cache(self) -> List[Eye]:
        return [x for x in (self.last_detected_left_eye, self.last_detected_right_eye) if x is not None]

    async def _successfully_refreshed_frame(self) -> bool:
        """Refreshes the frame."""
        if not self.capture_device:
            self.capture_device = cv2.VideoCapture(0)

        if not self.capture_device.isOpened():
            logging.warning("Camera could not be opened. Exiting.")
            await self.exit()
            return False

        successful, self.img = await run_in_executor(self.capture_device.read)

        if not successful:
            logging.warning("Camera not found. Exiting.")
            await self.exit()
            return False

        self.frame_counter += 1
        return True

    def _add_to_cache(self, eye: Eye):
        """Adds a captured eye to the cache depending on its type."""
        if not eye:
            return

        if eye.type is Eye.Type.LEFT:
            self.last_detected_left_eye = eye
        else:
            self.last_detected_right_eye = eye

    def parse_eye_coords_and_update_cache(self, detected_eye_coords: List[Tuple[int, int, int, int]]) -> None:
        """Parses the captured eye coordinates and updates the cache."""
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
                    # if the X coord difference is less than 20 pixels to the cached eye,
                    # its probably the same eye type as cached eye
                    x_diff = abs(coords[0] - cached_eye.coords[0])
                    if x_diff < 20:
                        eye_type = cached_eye.type

                # assign and update the other eye
                if eye_type is not Eye.Type.UNKNOWN:
                    other_eye = self.last_detected_right_eye if eye_type is Eye.Type.LEFT else self.last_detected_left_eye
                    other_eye.state = Eye.State.CLOSED

            eye = Eye(base_image=self.img, type=eye_type, state=Eye.State.OPEN, coords=coords)

            self._add_to_cache(eye)
            self._add_to_cache(other_eye)

    async def draw_gui(self):
        try:
            while not self.stopped:
                if self.img is not None:
                    # draw face
                    if not self.last_detected_face:
                        await draw_text(
                            self.img,
                            text="No face detected",
                            coords=(100, 100),
                            color=Color.RED)
                    else:
                        await self.last_detected_face.draw_name(self.img)
                        await self.last_detected_face.draw_rectangle(self.img)

                    # draw eyes
                    if len(self.eye_cache) <= 0:  # if the cache is empty
                        await draw_text(self.img, "No eyes detected", coords=(100, 150), color=Color.RED)
                    else:
                        # labels
                        for eye in self.eye_cache:
                            await eye.draw_name(self.img, face=self.last_detected_face)
                            await eye.draw_rectangle(self.img, face=self.last_detected_face)

                    # show the image
                    await run_in_executor(cv2.imshow, 'img', self.img)

                    # if the user presses q, exit
                    if await run_in_executor(cv2.waitKey, 1) == ord('q'):
                        return await self.exit()

                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            return

    async def show_graph(self):
        try:
            while not self.stopped:
                self.timer.show_graph()
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            return

    async def detect_eyes(self):
        try:
            while await self._successfully_refreshed_frame() and not self.stopped:
                # filtering
                self.timer.start()

                # flip the image (this might vary on camera device)
                self.img = await run_in_executor(
                    cv2.flip,
                    self.img,
                    1  # 0 = flip around x, 1 = flip around y, -1 = both
                )

                gray = await run_in_executor(cv2.cvtColor, self.img, cv2.COLOR_BGR2GRAY)  # convert to grayscale
                gray = await run_in_executor(cv2.bilateralFilter, gray, 5, 1, 1)  # remove impurities

                self.timer.capture("filtering", self.frame_counter)

                # detecting faces
                self.timer.start()
                faces: Optional[List[Face]] = [
                    Face(self.img, coord)
                    for coord in await run_in_executor(
                        FACE_CASCADE.detectMultiScale,
                        gray,
                        scaleFactor=1.3,  # the higher, the faster but less accurate
                        minNeighbors=5,  # the higher, the less false positives but higher chance of missing
                        minSize=(200, 200)
                    )
                ]
                self.timer.capture("face_detection", self.frame_counter)

                if len(faces) <= 0:
                    self.last_detected_face = None

                else:
                    # get the first face
                    face = faces[0]

                    # crop the filtered image using detected face's region
                    face_region = gray[face.y:face.y + face.height, face.x:face.x + face.width]

                    # detect eyes
                    self.timer.start()
                    detected_eyes = await run_in_executor(EYE_CASCADE.detectMultiScale, face_region, 1.3, 5,
                                                          minSize=(50, 50))
                    self.timer.capture("eye_detection", self.frame_counter)

                    # if we couldn't detect any new eye, mark previous eyes as closed
                    if len(detected_eyes) <= 0:
                        for eye in self.eye_cache:
                            eye.state = Eye.State.CLOSED
                    else:  # parse new detected eyes
                        self.parse_eye_coords_and_update_cache(detected_eyes)

                self.timer.capture("total", self.frame_counter, use_beginning=True)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            return

    async def exit(self):
        self.stopped = True

        await run_in_executor(cv2.destroyAllWindows)
        await run_in_executor(self.capture_device.release)
