import platform

# Cursor
if platform.system() == "Windows":
    from .cursor_win32 import WindowsCursor as Cursor
else:
    from .cursor_xlib import LinuxCursor as Cursor

from .image_object import *
from .sensor import *
