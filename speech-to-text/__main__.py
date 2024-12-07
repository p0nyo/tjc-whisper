import asyncio
import sys
import threading

from faster_whisper import WhisperModel
from .audio_transcriber import AppOptions
from .audio_transcriber import AudioTranscriber
from .utils.audio_util import base64_to_audio
from .utils.file_util import write_audio


transcriber: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None


def start_transcription():
    global transcriber, event_loop, thread
    try:
        whisper_model = WhisperModel(model_size_or_path="tiny.en")
        app_settings = AppOptions(audio_device=1)
        event_loop = asyncio.new_event_loop()
        
        filtered_transcribe_settings = {'language': 'en', 'task': 'transcribe', 'beam_size': 5, 'best_of': 5, 'patience': 1, 'length_penalty': 1, 'repetition_penalty': 1, 'no_repeat_ngram_size': 0, 'temperature': [0, 0.2, 0.4, 0.6, 0.8, 1], 'compression_ratio_threshold': 2.4, 'log_prob_threshold': -1, 'no_speech_threshold': 0.6, 'condition_on_previous_text': True, 'suppress_blank': True, 'suppress_tokens': [-1], 'without_timestamps': False, 'max_initial_timestamp': 1, 'word_timestamps': False, 'prepend_punctuations': '\\"\'“¿([{-', 'append_punctuations': '\\"\'.。,，!！?？:：”)]}、', 'vad_filter': False, 'vad_parameters': {'threshold': 0.5, 'min_speech_duration_ms': 250, 'max_speech_duration_s': 0, 'min_silence_duration_ms': 2000, 'speech_pad_ms': 400}}
        
        # AudioTranscriber class from audio_transcriber.py
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
        print(f"Error Message: {str(e)}")
        
# def stop_transcription():
#     global transcriber, event_loop, thread
    
if __name__ == "__main__":
    print("hello world")
    start_transcription()