import os
import requests
import fitz  # PyMuPDF
import azure.cognitiveservices.speech as speechsdk
import subprocess
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# 💬 Azure Keys & Endpoints 
VISION_KEY = os.getenv("VISION_KEY")
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT")



# 🔍 OCR for image files
def ocr_image(image_path):
    print("Performing OCR on image...")
    with open(image_path, "rb") as image_file:
        headers = {
            "Ocp-Apim-Subscription-Key": VISION_KEY,
            "Content-Type": "application/octet-stream"
        }
        params = {"language": "unk", "detectOrientation": "true"}
        ocr_url = VISION_ENDPOINT.rstrip('/') + "/vision/v3.2/ocr"

        response = requests.post(ocr_url, headers=headers, params=params, data=image_file)
        response.raise_for_status()
        result = response.json()

        extracted_text = ""
        for region in result.get("regions", []):
            for line in region.get("lines", []):
                line_text = " ".join([word["text"] for word in line["words"]])
                extracted_text += line_text + "\n"
    return extracted_text.strip()

# 📄 PDF text extraction using PyMuPDF
def extract_text_from_pdf(pdf_path):
    print("Extracting text from PDF using PyMuPDF...")
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

# 📂 TXT File Reading
def extract_text_from_txt(txt_path):
    print("Reading text from TXT file...")
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()

# 🌍 Translate text using Azure Translator
def translate_text(text, target_lang_code):
    print(f"Translating text to {target_lang_code}...")
    path = "/translate?api-version=3.0"
    params = f"&to={target_lang_code}"
    constructed_url = TRANSLATOR_ENDPOINT.rstrip('/') + path + params
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_REGION,
        'Content-type': 'application/json'
    }
    body = [{'text': text}]
    response = requests.post(constructed_url, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()
    return result[0]['translations'][0]['text']

# 🔊 Text-to-Speech with file output
def synthesize_speech(text, language_code):
    print("Synthesizing speech...")
    voice_map = {
        "en": "en-IN-PrabhatNeural",
        "hi": "hi-IN-MadhurNeural",
        "ta": "ta-IN-ValluvarNeural",
        "te": "te-IN-MohanNeural"
    }

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice_map.get(language_code, "en-IN-PrabhatNeural")

    audio_filename = "output_audio.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_filename)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("✅ Speech synthesized and saved to file.")
        return audio_filename
    else:
        print(f"❌ Speech synthesis failed: {result.reason} - {getattr(result, 'cancellation_details', None)}")
        return None

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def create_srt(subtitles, srt_path):
    with open(srt_path, 'w', encoding='utf-8') as f:
        for idx, start, end, text in subtitles:
            f.write(f"{idx}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")

def split_text_into_lines(text, max_chars=40):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return lines

def assign_timings(lines, total_duration):
    total_chars = sum(len(line) for line in lines)
    subtitles = []
    current_time = 0.0
    for i, line in enumerate(lines, 1):
        duration = (len(line) / total_chars) * total_duration if total_chars > 0 else 1.0
        start = current_time
        end = current_time + duration
        subtitles.append((i, start, end, line))
        current_time = end
    return subtitles

def get_audio_duration(audio_path):
    # Use ffprobe to get audio duration (requires ffmpeg installed)
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print("❌ Could not get audio duration, defaulting to 10 seconds.")
        return 10.0

def generate_mp4_with_subtitles(audio_file, background_image, text):
    srt_path = "temp_subtitles.srt"
    output_video = "final_video.mp4"

    duration = get_audio_duration(audio_file)
    lines = split_text_into_lines(text, max_chars=40)
    subtitles = assign_timings(lines, duration)
    create_srt(subtitles, srt_path)

    cmd = [
        'ffmpeg',
        '-y',
        '-loop', '1',
        '-i', background_image,
        '-i', audio_file,
        '-vf', f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&'",
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-t', str(duration),
        output_video
    ]
    print("🔧 Running ffmpeg to create video with subtitles...")
    subprocess.run(cmd, check=True)
    print(f"✅ Video created: {output_video}")