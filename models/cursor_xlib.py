import logging
import os
from typing import Tuple

from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input

from models.cursor import AbstractCursor


class LinuxCursor(AbstractCursor):
    def __init__(self, *args, **kwargs):
        self._display = Display(os.environ['DISPLAY'])

        super(LinuxCursor, self).__init__(*args, **kwargs)

    def get_screen_size(self) -> Tuple[int, int]:
        return self._display.screen().width_in_pixels, self._display.screen().height_in_pixels

    def get_current_pos(self) -> Tuple[int, int]:
        try:
            coord = self._display.screen().root.query_pointer()._data
        except RuntimeError:  # "Expected reply for request %s, but got %s.  Can't happen!"
            logging.exception("Could not get the current cursor position due to a Xlib error.")
            return self.x, self.y
        else:
            return coord["root_x"], coord["root_y"]

    def press_left_click(self) -> None:
        fake_input(self._display, X.ButtonPress, 1)
        self._sync_display()

    def release_left_click(self) -> None:
        fake_input(self._display, X.ButtonRelease, 1)
        self._sync_display()

    def press_right_click(self) -> None:
        fake_input(self._display, X.ButtonPress, 3)
        self._sync_display()

    def release_right_click(self) -> None:
        fake_input(self._display, X.ButtonRelease, 3)
        self._sync_display()

    def update_pos(self) -> None:
        fake_input(self._display, X.MotionNotify, x=self.x, y=self.y)
        self._sync_display()

    def _sync_display(self):
        try:
            self._display.sync()
        except RuntimeError:  # "Request reply to unknown request.  Can't happen!"
            logging.exception("Could not sync the display due to a Xlib error.")
