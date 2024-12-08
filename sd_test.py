import numpy as np
import soundfile as sf
import sounddevice as sd

print(sd.query_devices())

with sd.InputStream(device=1, samplerate=44100, channels=1) as stream:
    try:
        data = stream.read(132300)  # Read 3 seconds of audio
        sf.write("output.wav", np.array(data[0]), 44100)
        print("Sound input device works.")
    except Exception as e:
        print(str(e))