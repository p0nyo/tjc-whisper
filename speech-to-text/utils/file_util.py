import os
import soundfile as sf

script_dir = os.path.dirname(os.path.abspath(__file__))
python_root_dir = os.path.dirname(script_dir)
app_root_dir = os.path.dirname(python_root_dir)


def write_audio(dir_name: str, file_name: str, data):
    file_path = os.path.join(app_root_dir, dir_name, file_name + ".wav")

    # If a file with the same name already exists, remove it to forcefully write
    if os.path.exists(file_path):
        os.remove(file_path)

    sf.write(file_path, data, 16000)