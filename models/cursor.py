from __future__ import annotations

from typing import Tuple

import win32api
import win32con

__all__ = ['Cursor']


class Cursor(object):
    def __init__(self, x: int = 0, y: int = 0, use_latest_coords_from_windows: bool = True) -> None:
        self._x: int = x
        self._y: int = y

        # this option fetches the latest coordinates
        # each time we want to move the cursor.
        # this allows us to continue
        # wherever the cursor is dropped on by external sources.
        self.use_latest_coords_from_windows = use_latest_coords_from_windows

    @classmethod
    def get_with_current(cls) -> Cursor:
        return cls(*cls.get_current_pos())

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @x.setter
    def x(self, new_x: int = 0):
        if self.use_latest_coords_from_windows:
            self._update_coords_from_windows()

        if self.x != new_x:
            self._x = new_x
            self._update_pos()

    @y.setter
    def y(self, new_y: int = 0):
        if self.use_latest_coords_from_windows:
            self._update_coords_from_windows()

        if self.y != new_y:
            self._y = new_y
            self._update_pos()

    def move_in_y_axis(self, magnitude: int = 1):
        self.y += int(magnitude)

    def move_in_x_axis(self, magnitude: int = 1):
        self.x += int(magnitude)

    @staticmethod
    def left_click():
        Cursor.press_left_click()
        Cursor.release_left_click()

    @staticmethod
    def right_click():
        Cursor.press_right_click()
        Cursor.release_right_click()

    @staticmethod
    def press_left_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)

    @staticmethod
    def release_left_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    @staticmethod
    def press_right_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)

    @staticmethod
    def release_right_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

    @staticmethod
    def get_current_pos() -> Tuple[int, int]:
        return win32api.GetCursorPos()

    def _update_pos(self) -> None:
        win32api.SetCursorPos((self.x, self.y))

        # this is useful if we're getting out of bounds
        # or if the cursor was moved externally
        self._update_coords_from_windows()

    def _update_coords_from_windows(self) -> None:
        self._x, self._y = Cursor.get_current_pos()
