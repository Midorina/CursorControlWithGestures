from __future__ import annotations

import functools
import math
from enum import Enum
from typing import List, Tuple

import _dlib_pybind11
import numpy as np

from utils import drawing

__all__ = ['Eye', 'Face']


class DetectedObject:
    def __init__(self, base_image: np.ndarray, coordinates: Tuple[int, int, int, int]):
        self.base_image = base_image
        self.x1, self.y1, self.x2, self.y2 = coordinates

    @property
    def left_top(self) -> Tuple[int, int]:
        return self.x1, self.y1

    @property
    def right_bottom(self) -> Tuple[int, int]:
        return self.x2, self.y2

    @property
    def coordinates(self) -> Tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    def get_dlib_rectangle(self) -> _dlib_pybind11.rectangle:
        return _dlib_pybind11.rectangle(*self.coordinates)

    def draw(self):
        self.draw_name()
        self.draw_rectangle()

    def draw_name(self, **kwargs):
        drawing.draw_text(self.base_image, self.__class__.__name__, (self.x1 + 5, self.y1 - 5), **kwargs)

    def draw_rectangle(self, **kwargs):
        drawing.draw_rectangle(self.base_image, self.left_top, self.right_bottom, **kwargs)


class Face(DetectedObject):
    def __init__(self, base_image, coordinates):
        super(Face, self).__init__(base_image, coordinates)

    @classmethod
    def get_from_dlib_rectangle(cls, base_image: np.ndarray, rectangle: _dlib_pybind11.rectangle):
        top_left: _dlib_pybind11.point = rectangle.tl_corner()
        right_bottom: _dlib_pybind11.point = rectangle.br_corner()

        return cls(base_image, (top_left.x, top_left.y, right_bottom.x, right_bottom.y))


class Eye(DetectedObject):
    class Type(Enum):
        UNKNOWN = -1
        LEFT = 0
        RIGHT = 1

        def get_opposite(self) -> Eye.Type:
            if self == Eye.Type.UNKNOWN:
                raise Exception("No opposite of unknown eye type.")

            return Eye.Type(abs(self.value - 1))

    class State(Enum):
        CLOSED = 0
        OPEN = 1

        def get_opposite(self) -> Eye.State:
            return Eye.State(abs(self.value - 1))

    def __init__(self, base_image, face: Face, eye_type: Type, coordinates: Tuple[int, int, int, int],
                 landmark_points: List[Tuple[int, int]], state_threshold: float):
        super(Eye, self).__init__(base_image, coordinates)

        self.face = face
        self.type = eye_type
        self.state_threshold = state_threshold

        self.points: List[Tuple[int, int]] = landmark_points

    @classmethod
    def get_from_dlib_landmarks(cls, base_image: np.ndarray, face: Face, eye_type: Type,
                                eye_landmarks: List[int], all_landmarks: _dlib_pybind11.full_object_detection,
                                state_threshold: float = 6.0) -> Eye:
        landmarks = []
        for _landmark in eye_landmarks:
            point: _dlib_pybind11.point = all_landmarks.part(_landmark)
            landmarks.append((point.x, point.y))

        # generate rectangle coordinates
        highest_y = max(landmarks[1][1], landmarks[2][1]) - face.y1
        lowest_y = min(landmarks[4][1], landmarks[5][1]) - face.y1
        x1 = landmarks[0][0] - face.x1
        x2 = landmarks[3][0] - face.x1

        return cls(base_image, face, eye_type, (x1, highest_y, x2, lowest_y), landmarks, state_threshold)

    def draw(self):
        super().draw()
        self.draw_points()

    def draw_name(self, **kwargs) -> None:
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_text(
            self.base_image,
            f"{self.type.name.title()} {self.state.name.title()}",
            (self.face.x1 + self.x1 + 5, self.face.y1 + self.y1 - 5),
            color=color, font_size=1.0, **kwargs
        )

    def draw_rectangle(self, **kwargs) -> None:
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_rectangle(
            self.base_image,
            (self.face.x1 + self.x1, self.face.y1 + self.y1),
            (self.face.x1 + self.x2, self.face.y1 + self.y2),
            color=color, **kwargs
        )

    def draw_points(self, **kwargs) -> None:
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        for point in self.points:
            drawing.draw_point(
                self.base_image,
                point,
                color=color, **kwargs
            )

    @functools.cached_property
    def closeness_ratio(self) -> float:
        def euclidean_distance(point1: Tuple[int, int], point2: Tuple[int, int]):
            return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

        def midpoint(point1: Tuple[int, int], point2: Tuple[int, int]) -> Tuple[int, int]:
            return int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2)

        left_corner = self.points[0]
        right_corner = self.points[3]
        top_center = midpoint(self.points[1], self.points[2])
        bottom_center = midpoint(self.points[4], self.points[5])

        horizontal_length = euclidean_distance(left_corner, right_corner)
        vertical_length = euclidean_distance(top_center, bottom_center)

        ratio = horizontal_length / vertical_length

        return ratio

    @property
    def state(self) -> Eye.State:
        return Eye.State.CLOSED if self.closeness_ratio > self.state_threshold else Eye.State.OPEN
