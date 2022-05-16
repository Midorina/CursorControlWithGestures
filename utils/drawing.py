from datetime import datetime, timedelta
from enum import Enum
from typing import Tuple

import cv2

__all__ = ['Color', 'draw_text', 'draw_rectangle', 'TemporaryText']


class Color(Enum):
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)


def draw_text(img,
              text: str,
              coords: Tuple[int, int] = (100, 100),
              font=cv2.FONT_HERSHEY_PLAIN,
              font_size: float = 3,
              color: Color = Color.GREEN,
              thickness: int = 2):
    cv2.putText(img,
                text, coords,
                font, font_size,
                color.value, thickness)


def draw_rectangle(img,
                   left_top_coords: Tuple[int, int],
                   right_bottom_coords: Tuple[int, int],
                   color: Color = Color.GREEN,
                   thickness: int = 2):
    cv2.rectangle(img, left_top_coords, right_bottom_coords, color.value, thickness)


def draw_point(img,
               coords: Tuple[int, int],
               radius: int = 2,
               color: Color = Color.GREEN,
               thickness: int = 2):
    cv2.circle(img, coords, radius, color.value, thickness)


class TemporaryText(object):
    def __init__(self, text: str, duration_in_seconds: float = 1.0, color: Color = Color.BLUE):
        self.text = text
        self.color = color

        self.duration_in_seconds = duration_in_seconds
        self.init_time = datetime.now()

    def has_expired(self) -> bool:
        return datetime.now() > self.expiration_time

    @property
    def expiration_time(self):
        return timedelta(seconds=self.duration_in_seconds) + self.init_time

    def draw(self, img):
        draw_text(img, self.text, color=self.color)