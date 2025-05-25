from itertools import chain, product
from pathlib import Path
import tempfile
from typing import List, Tuple, TypeVar
import subprocess
import os
from loguru import logger
from molpal.logging import make_filter

logger.remove()

T = TypeVar("T")
U = TypeVar("U")


def get_temp_file():
    p_tmp = Path(tempfile.gettempdir()) / next(tempfile._get_candidate_names())
    return str(p_tmp)


def distribute_and_flatten(xs_yss: List[Tuple[T, List[U]]]) -> List[Tuple[T, U]]:
    """Distribute x over a list ys for each item in a list of 2-tuples and
    flatten the resulting lists.

    For each item in a list of Tuple[T, List[U]], distribute T over the List[U]
    to generate a List[Tuple[T, U]] and flatten the resulting list of lists.

    Example
    -------
    >>> xs_yys = [(1, ['a','b','c']), (2, ['d']), (3, ['e', 'f'])]
    >>> distribute_and_flatten(xs_yss)
    [(1, 'a'), (1, 'b'), (1, 'c'), (2, 'd'), (3, 'e'), (3, 'f')]

    Returns
    -------
    List[Tuple[T, U]]
        the distributed and flattened list
    """
    return list(chain(*[product([x], ys) for x, ys in xs_yss]))


def init_realtime_console(cmd: str, log_path: str):
    logger.remove()
    logger.add(log_path, format="<green>{time}</green> <level>{message}</level>", filter=make_filter("gromacs"))
    gr_logger = logger.bind(name="gromacs")
    try:
        # Run in the current working directory
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=os.getcwd()
        )

        # Reading output in real-time
        try:
            while True:
                stdout_line = process.stdout.readline()

                # Print lines if available
                if stdout_line:
                    # print(stdout_line, end='')
                    gr_logger.info(stdout_line.strip())

                # Break when the process ends and buffers are empty
                if not stdout_line and process.poll() is not None:
                    break
        except KeyboardInterrupt:
            process.terminate()
            raise

        # Wait for the process to finish
        process.stdout.close()
        process.wait()

        # Check if the command was successful
        if process.returncode == 0:
            print("Successfully!")
        else:
            print("Failed")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



if __name__ == "__main__":
    master_path = "/ifmdata/gsinenko/gsinenko/BRD4_tests/apo_structure_for_AL/master_script.sh"
    text_path = "/ifmdata/gsinenko/gsinenko/BRD4_tests/apo_structure_for_AL/folders_cycle.txt"

    cmd = ["bash", master_path, text_path]
    log_path = "/home/gsinenko/molpal/logs/gromacs_test.log"
    init_realtime_console(cmd, log_path)