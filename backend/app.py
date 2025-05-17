import sys
from flask import Flask, render_template, request, jsonify,send_file
import os
import json
import datetime
from werkzeug.utils import secure_filename
from tile_2.speech_to_text import transcribe_audio_file, transcribe_microphone
from dotenv import load_dotenv
load_dotenv()

# Add paths for tile 1, 3, and 4
sys.path.append(os.path.join(os.path.dirname(__file__), 'tile_1'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tile_3', 'edubot_blob_cosmos', 'summarizer'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tile_3', 'edubot_blob_cosmos', 'flashcard_generator'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tile_4'))

from summarizer import generate_summary
from flashcard_generator import generate_flashcards
from tile_4 import tts
from tile_1 import ocr_summarizer

# --- Azure Integration ---
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient

def upload_to_blob(blob_name, data):
    conn_str = os.getenv("AZURE_BLOB_CONN_STR")
    container_name = os.getenv("BLOB_RESULTS_CONTAINER")
    if not conn_str or not container_name:
        raise EnvironmentError("Azure Blob Storage connection string or results container name not set in environment variables")
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)

def save_to_cosmos(document):
    endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    key = os.getenv("AZURE_COSMOS_KEY")
    if not endpoint or not key:
        raise EnvironmentError("Azure Cosmos DB endpoint or key not set in environment variables")
    client = CosmosClient(endpoint, key)
    database = client.get_database_client(os.getenv("COSMOS_DATABASE"))
    container = database.get_container_client(os.getenv("COSMOS_CONTAINER"))
    container.upsert_item({
        "id": document["id"],
        "summary": document.get("summary"),
        "flashcards": document.get("flashcards"),
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
    })

print("TEMPLATE FOLDER:", os.path.abspath('../frontend/templates'))
print("TILE1 EXISTS:", os.path.exists(os.path.abspath('../frontend/templates/tile1.html')))
print("TILE4 EXISTS:", os.path.exists(os.path.abspath('../frontend/templates/tile4.html')))

# Tell Flask where to find your templates
app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# --- Tile 1 integration starts here ---

@app.route('/tile1')
def tile1():
    return render_template('tile1.html')

@app.route('/ocr_summarize', methods=['POST'])
def ocr_summarize():
    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext in ['.pdf']:
            result = ocr_summarizer.process_pdf_bytes(filepath)
        elif ext in ['.jpg', '.jpeg', '.png']:
            result = ocr_summarizer.process_image_bytes(filepath)
        elif ext in ['.pptx']:
            result = ocr_summarizer.process_pptx_text(filepath)
        else:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Unsupported file type'})
        os.remove(filepath)
        return jsonify({'success': True, **result})
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'error': str(e)})

# --- Tile 1 integration ends here ---

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    result = transcribe_audio_file(filepath)
    os.remove(filepath)
    return jsonify(result)

@app.route('/transcribe_microphone', methods=['POST'])
def transcribe_microphone_route():
    result = transcribe_microphone()
    return jsonify(result)

@app.route('/tile2')
def tile2():
    return render_template('tile2.html')

# --- Tile 3 integration starts here ---

@app.route('/tile3')
def tile3():
    return render_template('tile3.html')

@app.route('/generate_flashcards', methods=['POST'])
def generate_flashcards_route():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})
    summary = generate_summary(text)
    flashcards = generate_flashcards(text, summary, use_blooms=True)

    # --- Azure upload (optional, add your own logic for IDs) ---
    try:
        base_name = "web_input_" + datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%S")
        summary_file = f"{base_name}_summary_OCR.txt"
        flashcard_file = f"{base_name}_flashcards_OCR.json"
        upload_to_blob(summary_file, summary)
        upload_to_blob(flashcard_file, json.dumps(flashcards, indent=2, ensure_ascii=False))
        save_to_cosmos({
            "id": base_name,
            "summary": summary,
            "flashcards": flashcards
        })
        print(f"Azure upload successful for {base_name}")
    except Exception as e:
        print("Azure upload failed:", e)
    # -----------------------------------------------------------

    return jsonify({'success': True, 'summary': summary, 'flashcards': flashcards})

# --- Tile 3 integration ends here ---

# --- Tile 4 integration starts here ---

@app.route('/tile4')
def tile4():
    return render_template('tile4.html')

@app.route('/tts', methods=['POST'])
def tts_route():
    data = request.get_json()
    text = data.get('text')
    language = data.get('language', 'en')
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})
    try:
        audio_path = tts.synthesize_speech(text, language)
        if audio_path:
            return jsonify({'success': True, 'audio_url': '/download_tts_audio'})
        else:
            return jsonify({'success': False, 'error': 'Speech synthesis failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_tts_audio')
def download_tts_audio():
    audio_path = os.path.join(os.path.dirname(__file__), "output_audio.wav")
    if os.path.exists(audio_path):
        return send_file(audio_path, as_attachment=True)
    return "Audio file not found", 404

# --- Tile 4 integration ends here ---

@app.route('/test')
def test():
    return "Test route works!"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
