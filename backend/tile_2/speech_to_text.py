import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# Load environment variables from .env
load_dotenv()

speech_key = os.getenv("SPEECH_KEY")
speech_region = os.getenv("SPEECH_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

def transcribe_audio_file(audio_file_path):
    audio_config = speechsdk.AudioConfig(filename=audio_file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    done = False
    all_text = []

    def recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            all_text.append(evt.result.text)

    def stop_cb(evt):
        nonlocal done
        done = True

    recognizer.recognized.connect(recognized)
    recognizer.session_stopped.connect(stop_cb)
    recognizer.canceled.connect(stop_cb)

    recognizer.start_continuous_recognition()
    while not done:
        import time
        time.sleep(0.5)
    recognizer.stop_continuous_recognition()

    return {"success": True, "text": " ".join(all_text)}

def transcribe_microphone():
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    result = recognizer.recognize_once()
    return process_result(result)

def process_result(result):
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        text = result.text
        return {"success": True, "text": text}
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return {"success": False, "error": "No speech could be recognized"}
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        error_message = f"Canceled: {cancellation.reason}"
        if cancellation.reason == speechsdk.CancellationReason.Error:
            error_message += f"\nError details: {cancellation.error_details}"
        return {"success": False, "error": error_message}
