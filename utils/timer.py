from time import perf_counter

import matplotlib.pyplot as plt

__all__ = ['Timer']


class Timer:
    def __init__(self):
        self._beginning = None
        self._last_time = None

        self._time_data = dict()

    def start(self):
        self._last_time = perf_counter()
        if not self._beginning:
            self._beginning = self._last_time

    def capture(self, process_name: str, frame: int, use_beginning: bool = False):
        if not self._last_time:
            raise Exception("You need to start the timer before ending it.")

        now = perf_counter()
        if use_beginning:
            last_time = self._beginning
        else:
            last_time = self._last_time

        if process_name not in self._time_data.keys():
            self._time_data[process_name] = dict()

        self._time_data[process_name][frame] = now - last_time
        self._last_time = now

    def show_graph(self):
        # remove the first frame of face detection
        # because it initially takes too long for some reason
        self._time_data["face_detection"].pop(1)
        self._time_data["total"].pop(1)

        for processing_type, values in self._time_data.items():
            plt.plot(values.keys(), values.values(), label=processing_type, linewidth=1.0)

        plt.title("Processing Times")
        plt.ylabel("Seconds")
        plt.xlabel("Frames")
        plt.legend()
        plt.show()

        for processing_type, values in self._time_data.items():
            print(f"Average {processing_type} processing time:", sum(values.values()) / len(values))
