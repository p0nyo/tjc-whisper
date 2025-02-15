import asyncio
import functools
import queue
import numpy as np
import eel
import boto3
import soundfile as sf

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor

from .vad import Vad
from .utils.audio_util import create_audio_stream
from .utils.file_util import write_audio

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import errors
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/documents"]

class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 1
    noise_threshold: int = 5
    non_speech_threshold: float = 0.1
    time_limit: int = 30
    whisper_time_limit: int = 30
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
        app_options: AppOptions,

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
        self.time_counter = 0
        self.whisper_time_counter = 0
        self.time_limit = app_options.time_limit * 30
        self.whisper_time_limit = app_options.whisper_time_limit * 30
        # callback function is triggered every 32 milliseconds
        # if we want a time limit of roughly 1 second (1000 millisecond),
        # then time_limit = 31 (992 milliseconds), can use 30 for ease
        # time_limit conversion rate: 30 = 1 second
        self.audio_data_list = []
        self.all_audio_data_list = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None
        self.executor = ThreadPoolExecutor()
        self.creds = authenticate_user()
        self.boto_session = boto3.Session(profile_name="default")
    
    # used for transcribing the audio
    async def transcribe_audio(self):
        transcribe_settings = self.transcribe_settings.copy()
        transcribe_settings["without_timestamps"] = True
        transcribe_settings["word_timestamps"] = False
        try:
            translate = self.boto_session.client(service_name="translate", region_name="ap-southeast-2", use_ssl=True)
        except Exception as e:
            print(str(e))
        
        with self.executor as executor:
            while self.transcribing:
                try:
                    print(f"{'-'*80}")
                    # asynchronous task, fetches the audio from audio_queue by 
                    # running it in a separate thread 
                    # await is used to return control to the event loop running on the main thread
                    audio_data = await self.event_loop.run_in_executor(
                        executor, functools.partial(self.audio_queue.get, timeout=4.0)
                    )
                    
                    print("Pending: Grabbing audio data from audio queue . . .\n")

                    # create a partial function to run the transcribe function from whisper
                    func = functools.partial(
                        self.whisper_model.transcribe,
                        audio=audio_data,
                        **transcribe_settings
                    )
                    

                    # get the transcribed segments from the partial function ran 
                    # inside a separate thread pool
                    try:
                        transcription_task = self.event_loop.run_in_executor(executor, func)
                        segments, _ = await asyncio.wait_for(transcription_task, timeout=4)
                        print("Success: Transcription Task Completed.")
                    except Exception as e:
                        print(f"Failure: {str(e)}")
                        continue

                    for segment in segments:
                        print("\nSuccess: Transcription Segments Found.\n")

                        transcription_text = segment.text + " "
                        print(f"Transcription Text: '{transcription_text}'") 
                        # eel.on_receive_message(transcription_text)

                        transcription_word_list = transcription_text.split()
                        print(transcription_word_list)

                        result = translate.translate_text(Text=segment.text, 
                        SourceLanguageCode="zh", 
                        TargetLanguageCode="en")

                        translation_text = result.get("TranslatedText") + " "
                        eel.on_receive_message(transcription_text + " " + translation_text)
                        print(f"Translation Text: {translation_text}\n") 

                        document_id = append_to_doc(self.creds, translation_text)
                        print(f"Success: Appended to Google Doc ID: '{document_id}'.")
                        
                        translation_word_list = translation_text.split()
                        print(translation_word_list)

                # if queue is empty skip to next iteration in queue
                except queue.Empty:
                    print("Failure: Audio Queue is empty")
                
                # if other exceptions caught then print on console
                except Exception as e:
                    print(str(e))
    
    # used for processing the final audio file after transcription stops
    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        is_speech = self.vad.is_speech(audio_data)
        # flatten(): turns a 2D array into a 1D array
        print(self.whisper_time_counter)
        self.time_counter += 1
        self.whisper_time_counter += 1 
        # if there is speech reset silence counter to 0 and append 
        # flattened audio to data list
        if is_speech:
            self.silence_counter = 0
            self.audio_data_list.append(audio_data.flatten())
        
        # otherwise increment silence counter and add flattened audio to 
        # data list only if we want to include
        else:
            print("silence")
            self.silence_counter += 1

        # based on self.time_limit, the time_counter increments until it hits the limit
        # automatically dumping whatever is on the audio data list to the audio queue
        # where it is sent to
        if (not is_speech and self.silence_counter > self.app_options.silence_limit) or (self.time_counter >= self.time_limit):
            # handles prolonged silence, if silence counter reaches the limit
            # the silence counter is reset to 0

            if (self.silence_counter > self.app_options.silence_limit) or (self.whisper_time_counter > self.whisper_time_limit):
                self.whisper_time_counter = 0
                self.all_audio_data_list.clear()

            self.silence_counter = 0
            self.time_counter = 0
            # self.silence_counter += 1
            # creates audio file if option enabled
            # if self.app_options.create_audio_file:
            #     self.all_audio_data_list.extend(self.audio_data_list)
                
            # short segments of audio data often contain transient noise
            # noise threshold can filter out these short segments
            if len(self.audio_data_list) > self.app_options.noise_threshold:
                # self.save_audio_file(self.audio_data_list, "output.wav")
                print("Pending: Adding audio data to the audio queue . . .")
                self.all_audio_data_list.extend(self.audio_data_list)
                concatenate_audio_data = np.concatenate(self.all_audio_data_list)
                self.audio_data_list.clear()
                self.audio_queue.put(concatenate_audio_data)
            else:
                self.audio_data_list.clear()


    def save_audio_file(self, audio_data_list, filename, samplerate=16000):
        # Concatenate all audio data in the list
        audio_data = np.concatenate(audio_data_list)
    
        # Save the concatenated audio data to a file
        sf.write(filename, audio_data, samplerate)

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
            try:
                self._transcribe_task = asyncio.run_coroutine_threadsafe(
                    self.transcribe_audio(), self.event_loop
                )
            except Exception as e:
                print(str(e))
            print(f"Transcription started with a time limit of {self.time_limit/30} seconds . . .")
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
            
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=False) 
                print("ThreadPoolExecutor shut down.")

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

def test_api_keys():
    try:
        # check to see if google docs API credentials are valid
        append_to_doc(authenticate_user(), " ")
        print("Success: Google Docs API Credentials Verified.")
    except Exception as e:
        error_message = str(e)
        raise Exception(error_message)

    try:
        boto_session = boto3.Session(profile_name="default")
        translate = boto_session.client(service_name="translate", region_name="ap-southeast-2", use_ssl=True)
        # check to see if aws API credentials are valid
        test = translate.translate_text(Text="the", 
                    SourceLanguageCode="en", 
                    TargetLanguageCode="en")
        translate_test = test.get("TranslatedText")
        print("Success: AWS Translate API Credentials Verified.")
    except Exception as e:
        error_message = str(e)
        raise Exception(error_message + " (Run 'aws configure sso')")

def authenticate_user():
    """Calls the Apps Script API."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    return creds

def append_to_doc(creds, text):
    try:
        service = build('docs', 'v1', credentials=creds)

        document_id="1gUf_TZvFwVfvWT74IKsh5YmJ0Fo8HoRtGxzHPPBVHUY"

        document = service.documents().get(documentId=document_id).execute()
        end_index = document['body']['content'][-1]['endIndex']

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': end_index - 1,
                    },
                    'text': text,
                }
            },
        ]

        service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

        return document_id
    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content)