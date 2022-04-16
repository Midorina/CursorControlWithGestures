from __future__ import annotations

from enum import Enum
from typing import Tuple

import numpy as np

from utils import drawing

__all__ = ['Eye', 'Face']


class DetectedObject:
    def __init__(self, base_image: np.ndarray, coordinates: Tuple[int, int, int, int]):
        self.base_image = base_image
        self.x, self.y, self.width, self.height = coordinates

    @property
    def coordinates(self) -> Tuple[int, int]:
        return self.x, self.y

    def draw_name(self, img, **kwargs):
        drawing.draw_text(img, self.__class__.__name__, (self.x + 5, self.y - 5), **kwargs)

    def draw_rectangle(self, img, **kwargs):
        drawing.draw_rectangle(img, self.coordinates, (self.x + self.width, self.y + self.height), **kwargs)


class Face(DetectedObject):
    def __init__(self, base_image, coordinates):
        super(Face, self).__init__(base_image, coordinates)


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

    def __init__(self, base_image, face: Face, eye_type: Type, state: State, coordinates):
        super(Eye, self).__init__(base_image, coordinates)

        self.face = face
        self.type = eye_type
        self.state = state

    def draw_name(self, img, **kwargs) -> None:
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_text(
            img,
            f"{self.type.name.title()} {self.state.name.title()}",
            (self.face.x + self.x + 5, self.face.y + self.y - 5),
            color=color, font_size=1.0, **kwargs
        )

    def draw_rectangle(self, img, **kwargs) -> None:
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_rectangle(
            img,
            (self.face.x + self.x, self.face.y + self.y),
            (self.face.x + self.x + self.width, self.face.y + self.y + self.height),
            color=color, **kwargs
        )
