#
# 功能: 定义时间测量工具。
#
import time
import logging


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start


def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.getLogger(func.__module__).debug(
            f"{func.__name__} took {end - start:.2f}s"
        )
        return result

    return wrapper
