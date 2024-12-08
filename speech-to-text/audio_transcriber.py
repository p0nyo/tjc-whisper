import asyncio
import functools
import queue
import numpy as np
import eel

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor

from .vad import Vad
from .utils.audio_util import create_audio_stream
from .utils.file_util import write_audio


class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 8
    noise_threshold: int = 5
    non_speech_threshold: float = 0.1
    include_non_speech: bool = False
    create_audio_file: bool = False
    use_websocket_server: bool = False
    use_openai_api: bool = False

class AudioTranscriber:
    def __init__(
        self,
        event_loop: asyncio.AbstractEventLoop,
        whisper_model: WhisperModel,
        transcribe_settings: dict,
        app_options: AppOptions
        # websocket_server: WebSocketServer
        # openai_api: OpenAIAPI,
    ):

        self.event_loop = event_loop
        self.whisper_model: WhisperModel = whisper_model
        self.transcribe_settings = transcribe_settings
        self.app_options = app_options
        # self.websocket_server = websocket_server
        # self.openai_api = openai_api
        self.vad = Vad(app_options.non_speech_threshold)
        self.silence_counter: int = 0
        self.audio_data_list = []
        self.all_audio_data_list = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None
    
    # used for transcribing the audio
    async def transcribe_audio(self):
        transcribe_settings = self.transcribe_settings.copy()
        transcribe_settings["without_timestamps"] = True
        transcribe_settings["word_timestamps"] = False
        
        with ThreadPoolExecutor() as executor:
            while self.transcribing:
                try:
                    # asynchronous task, fetches the audio from audio_queue by 
                    # running it in a separate thread 
                    # await is used to return control to the event loop running on the main thread
                    audio_data = await self.event_loop.run_in_executor(
                        executor, functools.partial(self.audio_queue.get, timeout=3.0)
                    )
                    
                    # create a partial function to run the transcribe function from whisper
                    func = functools.partial(
                        self.whisper_model.transcribe,
                        audio=audio_data,
                        **transcribe_settings
                    )
                    
                    # get the transcribed segments from the partial function ran 
                    # inside a separate thread pool
                    segments, _ = await self.event_loop.run_in_executor(executor, func)
                    
                    for segment in segments:
                        eel.on_receive_message(segment.text)
                        print(segment.text)
                        
                # if queue is empty skip to next iteration in queue
                except queue.Empty:
                    continue
                
                # if other exceptions caught then print on console
                except Exception as e:
                    print(str(e))
    
    # used for processing the final audio file after transcription stops
    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        is_speech = self.vad.is_speech(audio_data)
        
        # flatten(): turns a 2D array into a 1D array
        
        # if there is speech reset silence counter to 0 and append 
        # flattened audio to data list
        if is_speech:
            self.silence_counter = 0
            self.audio_data_list.append(audio_data.flatten())
        
        # otherwise increment silence counter and add flattened audio to 
        # data list only if we want to include
        else:
            self.silence_counter += 1
            if self.app_options.include_non_speech:
                self.all_audio_data_list.append(audio_data.flatten())
        
        # handles prolonged silence, if silence counter reaches the limit
        # the silence counter is reset to 0
        if not is_speech and self.silence_counter > self.app_options.silence_limit:
            self.silence_counter = 0
        
            # creates audio file if option enabled
            if self.app_options.create_audio_file:
                self.all_audio_data_list.extend(self.audio_data_list)
                
            # short segments of audio data often contain transient noise
            # noise threshold can filter out these short segments
            if len(self.audio_data_list) > self.app_options.noise_threshold:
                concatenate_audio_data = np.concatenate(self.audio_data_list)
                self.audio_data_list.clear()
                self.audio_queue.put(concatenate_audio_data)
            else:
                self.audio_data_list.clear()

    # used to start the live transcription
    async def start_transcription(self):
        try:
            self.transcribing = True
            self.stream = create_audio_stream(
                self.app_options.audio_device, self.process_audio
            )
            self.stream.start()
            self._running.set()
            
            # send the transcribe function to run in a separate thread
            self._transcribe_task = asyncio.run_coroutine_threadsafe(
                self.transcribe_audio(), self.event_loop
            )
            print("Transcription started . . .")
            while self._running.is_set():
                await asyncio.sleep(1)
        
        except Exception as e:
            print(str(e))
    
    # used to stop the live transcription
    async def stop_transcription(self):
        try: 
            # stop the transcribing task started in start_transcription()
            self.transcribing = False
            if self._transcribe_task is not None:
                self.event_loop.call_soon_threadsafe(self._transcribe_task.cancel)
                self._transcribe_task = None
            
            # checks if create_audio_file is enabled and there is data in the list
            # i have manually disabled this
            if self.app_options.create_audio_file and len(self.all_audio_data_list) > 0:
                audio_data = np.concatenate(self.all_audio_data_list)
                self.all_audio_data_list.clear()
                write_audio("audio", "voice", audio_data)
                # self.batch_transcribe_audio(audio_data)
            
            # stop and close the stream
            if self.stream is not None:
                self._running.clear()
                self.stream.stop()
                self.stream.close()
                self.stream = None
                print("Transcription stopped.")
            else:
                print("No active stream to stop")   
                 
        except Exception as e:
            print(str(e))
        