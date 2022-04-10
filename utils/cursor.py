import time

import win32api
import win32con

__all__ = ['CursorController']


class CursorPosition(object):
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    @classmethod
    def get_current(cls):
        x, y = win32api.GetCursorPos()

        return cls(x, y)


class CursorController(object):
    def __init__(self) -> None:
        self.cursor_position = CursorPosition.get_current()

    def _update_cursor(self):
        win32api.SetCursorPos((self.cursor_position.x, self.cursor_position.y))

    def move_in_y_axis(self, magnitude: int = 1):
        self.cursor_position.y += int(magnitude)
        self._update_cursor()

    def move_in_x_axis(self, magnitude: int = 1):
        self.cursor_position.x += int(magnitude)
        self._update_cursor()

    @staticmethod
    def left_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.07)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    @staticmethod
    def right_click():
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
        time.sleep(0.07)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
