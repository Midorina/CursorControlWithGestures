from enum import Enum, auto
from typing import Tuple

import numpy as np

from utils import drawing

__all__ = ['Eye', 'Face']


class DetectedObject:
    def __init__(self, base_image: np.ndarray, coords: Tuple[int, int, int, int]):
        self.base_image = base_image
        self.x, self.y, self.width, self.height = coords

    @property
    def coords(self) -> Tuple[int, int]:
        return self.x, self.y

    def draw_name(self, img, **kwargs):
        drawing.draw_text(img, self.__class__.__name__, (self.x + 5, self.y - 5), **kwargs)

    def draw_rectangle(self, img, **kwargs):
        drawing.draw_rectangle(img, self.coords, (self.x + self.width, self.y + self.height), **kwargs)


class Face(DetectedObject):
    def __init__(self, base_image, coords):
        super(Face, self).__init__(base_image, coords)


class Eye(DetectedObject):
    class Type(Enum):
        LEFT = auto()
        RIGHT = auto()
        UNKNOWN = auto()

    class State(Enum):
        CLOSED = 0
        OPEN = 1

    def __init__(self, base_image, type: Type, state: State, coords):
        super(Eye, self).__init__(base_image, coords)

        self.type = type
        self.state = state

    # override
    def draw_name(self, img, face: Face, **kwargs):
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_text(
            img,
            f"{self.type.name.title()} {self.state.name.title()}",
            (face.x + self.x + 5, face.y + self.y - 5),
            color=color, font_size=1.0, **kwargs
        )

    # override
    def draw_rectangle(self, img, face: Face, **kwargs):
        color = drawing.Color.RED if self.state is self.State.CLOSED else drawing.Color.GREEN
        drawing.draw_rectangle(
            img,
            (face.x + self.x, face.y + self.y),
            (face.x + self.x + self.width, face.y + self.y + self.height),
            color=color, **kwargs
        )
