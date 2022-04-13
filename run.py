import logging

from main import MainController


class Runner:
    def __init__(self):
        self.prepare_logger()
        self.main_controller = MainController()

    @staticmethod
    def prepare_logger():
        logging.basicConfig(
            style='{',
            format='[{asctime}.{msecs:.0f}] [{levelname:<7}] {name}: {message}',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG)

    def run(self):
        try:
            self.main_controller.run()
        except Exception as e:
            logging.exception(e)
            self.main_controller.stop()


if __name__ == '__main__':
    Runner().run()
