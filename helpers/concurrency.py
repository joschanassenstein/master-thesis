from time import sleep
from typing import List
from itertools import cycle
from multiprocessing import Process


def visualize(producers: List[Process]) -> None:
    """Visualization of multiple parallelized processes on the command line.
        This function displays the name of each process and an indicator of its status.
        It is intended to run on the main thread and resumes once all processes have finished.
    """
    symbols = cycle(["|", "/", "-", "\\"])

    print("\nExtracting data:")

    while True:
        symbol = next(symbols)

        current_states = [
            f" {process.name} {symbol if process.is_alive() else '+'}" for process in producers]
        print(" , ".join(current_states), end="\r")

        if not any([process.is_alive() for process in producers]):
            break

        sleep(0.2)

    print()
