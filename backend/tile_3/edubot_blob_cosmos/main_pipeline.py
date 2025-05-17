"""
main_pipeline.py - Summarization + Flashcard Generator (Supports Local File Input)

Responsibilities:
1. Accept file input (from local or blob)
2. Run summarization and flashcard generation
3. Upload results to Blob and Cosmos DB (if enabled)
"""

import os
import json
import re
import datetime
import argparse
from transformers import pipeline
import language_tool_python
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print("AZURE_BLOB_CONN_STR =", os.getenv("AZURE_BLOB_CONN_STR"))
print("BLOB_RESULTS_CONTAINER =", os.getenv("BLOB_RESULTS_CONTAINER"))

# --- Azure Integration ---
def download_from_blob(blob_name):
    conn_str = os.getenv("AZURE_BLOB_CONN_STR")
    container_name = os.getenv("BLOB_UPLOAD_CONTAINER")
    if not conn_str or not container_name:
        raise EnvironmentError("Azure Blob Storage connection string or upload container name not set in environment variables")
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
    return blob_client.download_blob().readall().decode("utf-8")

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
        "summary": document["summary"],
        "flashcards": document["flashcards"],
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

# --- Text Processing ---
def clean_text_general(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page\s*\d+[:.]?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\.', '', text)
    text = re.sub(r'[•·]', '-', text)
    text = re.sub(r'(\w)[.,](\w)', r'\1. \2', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    return text.strip()

def correct_grammar(text):
    tool = None
    try:
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text)
        return language_tool_python.utils.correct(text, matches)
    finally:
        if tool:
            tool.close()

def chunk_text(text, chunk_size=1024, overlap=200):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def summarize_text(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    chunks = chunk_text(text)
    summary = ""
    for chunk in chunks:
        result = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
        summary += result[0]["summary_text"] + " "
    return summary.strip()

def generate_flashcards(text, summary):
    qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
    sentences = [s.strip() for s in re.split(r'[.!?]', summary) if len(s.strip().split()) > 5]
    templates = [
        "Explain: {}", "What does this mean: {}",
        "Summarize: {}", "Why is this important: {}"
    ]
    flashcards = []
    for i, s in enumerate(sentences[:10]):
        template = templates[i % len(templates)]
        short_s = (s[:80] + "…") if len(s) > 80 else s
        question = template.format(short_s)
        try:
            answer = qa_pipeline(question=question, context=text)
            if answer['score'] > 0.3 and answer['answer'].strip():
                flashcards.append({
                    "question": question,
                    "answer": answer['answer'].strip()
                })
        except Exception:
            continue
    return flashcards

def process_text(text):
    cleaned = clean_text_general(text)
    corrected = correct_grammar(cleaned)
    summary = summarize_text(corrected)
    flashcards = generate_flashcards(corrected, summary)
    return summary, flashcards

# --- Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="Process text file for summarization and flashcards")
    parser.add_argument("--input_file", required=True, help="Path to input .txt file")
    parser.add_argument("--upload", action="store_true", help="Upload results to Azure Blob and Cosmos DB")
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    summary, flashcards = process_text(text)

    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    summary_file = f"{base_name}_summary_OCR.txt"
    flashcard_file = f"{base_name}_flashcards_OCR.json"

    # Save locally
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    with open(flashcard_file, 'w', encoding='utf-8') as f:
        json.dump(flashcards, f, indent=2, ensure_ascii=False)

    print(f"Summary and flashcards saved to:\n{summary_file}\n{flashcard_file}")

    # Optional Azure upload
    if args.upload:
        upload_to_blob(summary_file, summary)
        upload_to_blob(flashcard_file, json.dumps(flashcards, indent=2, ensure_ascii=False))
        save_to_cosmos({
            "id": base_name,
            "summary": summary,
            "flashcards": flashcards
        })
        print("Results uploaded to Azure.")

if __name__ == "__main__":
    main()