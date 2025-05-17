import os
import json
import azure.functions as func
from main_pipeline import process_text, upload_to_blob, save_to_cosmos

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
    except:
        return func.HttpResponse("Invalid JSON input", status_code=400)

    text = data.get("text")
    if not text:
        return func.HttpResponse("Missing 'text' field", status_code=400)

    try:
        summary, flashcards = process_text(text)

        file_id = data.get("id", "default_id")
        upload = data.get("upload", False)

        if upload:
            upload_to_blob("results", f"{file_id}_summary_OCR.txt", summary)
            upload_to_blob("results", f"{file_id}_flashcards_OCR.json", json.dumps(flashcards, indent=2, ensure_ascii=False))
            save_to_cosmos({
                "id": file_id,
                "summary": summary,
                "flashcards": flashcards
            })

        result = {
            "summary": summary,
            "flashcards": flashcards
        }
        return func.HttpResponse(json.dumps(result, ensure_ascii=False, indent=2), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)