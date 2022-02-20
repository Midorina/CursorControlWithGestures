import asyncio
import logging
from typing import Coroutine, List

from blink_detector import BlinkDetector


class Manager:
    def __init__(self):
        # main module
        self.blink_detector = BlinkDetector()

        # async stuff
        self.loop = asyncio.get_event_loop()
        self.async_tasks: List[asyncio.Task] = []

    def prepare_logger(self):
        logging.basicConfig(
            # format='[{asctime}.{msecs:.0f}] [{levelname:<7}] {name}: {message}',
            # datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG)

    def start(self):
        self.prepare_logger()

        self.async_tasks.append(asyncio.ensure_future(self.initiate_all_modules(), loop=self.loop))

        try:
            self.loop.run_forever()
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.loop.run_until_complete(self.shutdown())
        finally:
            self.loop.stop()
            self.loop.close()

    async def initiate_all_modules(self):
        # frame capturing and eye detection module
        self.create_task(self.blink_detector.detect_eyes())
        # gui module
        self.create_task(self.blink_detector.draw_gui())
        # graph module
        self.create_task(self.blink_detector.show_graph())

    def create_task(self, coro: Coroutine):
        self.async_tasks.append(self.loop.create_task(coro))

    async def shutdown(self):
        # shutdown the blink detector
        await self.blink_detector.exit()

        # make sure all tasks are cancelled
        for task in self.async_tasks:
            if not task.cancelled():
                task.cancel()

        self.async_tasks = []
