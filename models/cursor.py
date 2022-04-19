from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Tuple


class AbstractCursor(ABC):
    def __init__(
            self,
            x: int = 0, y: int = 0,
            allow_external_movement: bool = True,
            use_center_as_starting_point: bool = True) -> None:
        # starting point
        if use_center_as_starting_point is True:
            w, h = self.get_screen_size()
            self._x, self._y = w // 2, h // 2
        else:
            self._x, self._y = x, y

        # if this is option is true,
        # we fetch the latest coordinates each time the cursor needs to move.
        # this allows us to continue wherever the cursor is dropped on by external sources.
        self.allow_external_movement = allow_external_movement

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @x.setter
    def x(self, new_x: int = 0) -> None:
        if self.x == new_x:
            return

        self._x = new_x
        self.update_pos()

    @y.setter
    def y(self, new_y: int = 0) -> None:
        if self.y == new_y:
            return

        self._y = new_y
        self.update_pos()

    def move_in_y_axis(self, magnitude: int = 1) -> int:
        if self.allow_external_movement:
            self._update_coords_from_os()

        self.y += int(magnitude)

        return self.y

    def move_in_x_axis(self, magnitude: int = 1) -> int:
        if self.allow_external_movement:
            self._update_coords_from_os()

        self.x += int(magnitude)

        return self.x

    def left_click(self) -> None:
        self.press_left_click()
        time.sleep(0.05)
        self.release_left_click()

    def right_click(self) -> None:
        self.press_right_click()
        time.sleep(0.05)
        self.release_right_click()

    def _update_coords_from_os(self) -> None:
        # this is useful if we're getting out of bounds
        # or if the cursor was moved externally
        self._x, self._y = self.get_current_pos()

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        raise NotImplementedError

    @abstractmethod
    def get_current_pos(self) -> Tuple[int, int]:
        raise NotImplementedError

    @abstractmethod
    def press_left_click(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def release_left_click(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def press_right_click(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def release_right_click(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_pos(self) -> None:
        raise NotImplementedError
