from typing import Tuple

import win32api
import win32con

from models.cursor import AbstractCursor


class WindowsCursor(AbstractCursor):
    def __init__(self, *args, **kwargs):
        super(WindowsCursor, self).__init__(*args, **kwargs)

    def get_screen_size(self) -> Tuple[int, int]:
        return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

    def get_current_pos(self) -> Tuple[int, int]:
        return win32api.GetCursorPos()

    def press_left_click(self) -> None:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)

    def release_left_click(self) -> None:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def press_right_click(self) -> None:
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)

    def release_right_click(self) -> None:
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

    def update_pos(self) -> None:
        win32api.SetCursorPos((self.x, self.y))

    def key_is_pressed(self, key: str):
        return win32api.GetAsyncKeyState(ord(key)) != 0
