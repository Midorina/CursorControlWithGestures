import logging

from blink_detector import BlinkDetector


class Runner:
    def __init__(self):
        self.prepare_logger()
        self.blink_detector = BlinkDetector()

    def prepare_logger(self):
        logging.basicConfig(
            # format='[{asctime}.{msecs:.0f}] [{levelname:<7}] {name}: {message}',
            # datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG)

    def run(self):
        self.blink_detector.start()


if __name__ == '__main__':
    Runner().run()
