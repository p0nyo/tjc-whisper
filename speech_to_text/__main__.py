import asyncio
import sys
import threading
import eel

from faster_whisper import WhisperModel
from .audio_transcriber import AppOptions
from .audio_transcriber import AudioTranscriber
from .audio_transcriber import test_api_keys

eel.init("web")

transcriber: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None

@eel.expose
def start_transcription():
    global transcriber, event_loop, thread
    try:
        filtered_app_settings = {'audio_device': 1, 
                                 'silence_limit': 1, 
                                 'noise_threshold': 8, 
                                 'non_speech_threshold': 0.1, 
                                 'time_limit': 3,
                                 'whisper_time_limit': 30,
                                 'include_non_speech': False, 
                                 'create_audio_file': False, 
                                 'use_websocket_server': False, 
                                 'use_openai_api': False}
        # Model Options: 
        # tiny, tiny.en, base, base.en, small, small.en, medium
        # medium.en, large-v1, large-v2, large-v3, distil-large-v2, distil-medium.en
        # distil-small.en, distil-large-v3

        # Device Options:
        # cpu, cuda, auto
        # cuda is gpu
        # need to download cuda if running it
        filtered_model_settings = {'model_size_or_path': 'large-v2', 
                                   'device': 'cuda', 
                                   'device_index': 0, 
                                   'compute_type': 'default', 
                                   'cpu_threads': 0, 
                                   'num_workers': 1, 
                                   'local_files_only': False}
        filtered_transcribe_settings = {'language': 'zh', 
                                        'task': 'transcribe', 
                                        'log_progress': True,
                                        'beam_size': 5, 
                                        'best_of': 5, 
                                        'patience': 1, 
                                        'length_penalty': 1, 
                                        'repetition_penalty': 1, 
                                        'no_repeat_ngram_size': 0, 
                                        'temperature': [0, 0.2, 0.4, 0.6, 0.8, 1], 
                                        'compression_ratio_threshold': 2.4, 
                                        'log_prob_threshold': -1, 
                                        'no_speech_threshold': 0.6, 
                                        'condition_on_previous_text': True, 
                                        'suppress_blank': True, 
                                        'suppress_tokens': [-1], 
                                        'without_timestamps': False, 
                                        'max_initial_timestamp': 1, 
                                        'word_timestamps': False, 
                                        'multilingual': False,
                                        'prepend_punctuations': '\\"\'“¿([{-', 
                                        'append_punctuations': '\\"\'.。,，!！?？:：”)]}、', 
                                        'vad_filter': False, 
                                        'vad_parameters': {'threshold': 0.5, 'min_speech_duration_ms': 250, 'max_speech_duration_s': 0, 'min_silence_duration_ms': 2000, 'speech_pad_ms': 400}}
        
        whisper_model = WhisperModel(**filtered_model_settings)
        app_settings = AppOptions(**filtered_app_settings)
        event_loop = asyncio.new_event_loop()
                
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
        
@eel.expose
def stop_transcription():
    global transcriber, event_loop, thread
    # if transcriber is None:
    #     return
    transcriber_future = asyncio.run_coroutine_threadsafe(
        transcriber.stop_transcription(), event_loop
    )
    
    transcriber_future.result()
    
    if thread.is_alive():
        event_loop.call_soon_threadsafe(event_loop.stop)
        thread.join()
    event_loop.close()
    transcriber = None
    event_loop = None
    thread = None
    
    
    
def on_close(page, sockets):
    print(page, "was closed")
    if transcriber and transcriber.transcribing:
        stop_transcription()
        print("Stopped transcription.")
    if hasattr(transcriber, 'executor') and transcriber.executor:
        transcriber.executor.shutdown(wait=False)
        print("ThreadPoolExecutor shut down.")

    sys.exit()
    
if __name__ == "__main__":
    print("Opening Client . . .\n")
    try:
        test_api_keys()
        print("Success: Client Opened.\n")
        eel.start("index.html", size=(1024, 900), close_callback=on_close)
    except Exception as e:
        print(str(e))
        print("\nFailure: Client Closed.")