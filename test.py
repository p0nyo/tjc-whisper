import functools
import queue


def add_two(num1, num2):
    return num1 + num2

add_one = functools.partial(add_two, num2=1)

print(add_one(1))

audio_queue = queue.Queue()

