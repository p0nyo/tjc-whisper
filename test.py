# import functools
# import queue


# def add_two(num1, num2):
#     return num1 + num2

# add_one = functools.partial(add_two, num2=1)

# print(add_one(1))

# audio_queue = queue.Queue()

import sounddevice as sd

# List all available audio devices
print("Available audio devices:")
print(sd.query_devices())

# Get the default input device index
default_device = sd.default.device[0]  # [0] is input, [1] is output
print(f"Default input device index: {default_device}")


