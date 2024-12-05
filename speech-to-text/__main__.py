import asyncio
import sys
import threading

from faster_whisper import WhisperModel
from .audio_transcriber import AppOptions
from .audio_transcriber import AudioTranscriber
# from .utils.audio_util import get_valid_input_devices, base64_to_audio
from .utils.file_util import read_json, write_json, write_audio


transcriber: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None


def start_transcription():
    global transcriber, event_loop, thread, websocket_server, openai_api
    try:
        whisper_model = WhisperModel()
        app_settings = AppOptions()
        event_loop = asyncio.new_event_loop()
        
        transcriber = AudioTranscriber(
            event_loop,
            whisper_model,
            filtered_transcribe_settings,
            app_settings,
        )
        asyncio.set_event_loop(event_loop)
        thread = threading.Thread(target=event_loop.run_forever, daemon=True)
        thread.start()
        
        asyncio.run_coroutine_threadsafe(transcriber.start_transcription(), event_loop)
    
    except Exception as e:
        print(str(e))