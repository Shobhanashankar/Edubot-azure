import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import json
import azure.functions as func
from .flashcard_generator import generate_flashcards, generate_summary

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🧠 Received request for flashcard generation.")

    try:
        text = req.get_json().get("text", "")
        use_blooms = req.get_json().get("use_blooms", True)

        if not text:
            return func.HttpResponse("Missing 'text' in request body.", status_code=400)

        summary = generate_summary(text)
        flashcards = generate_flashcards(text, summary, use_blooms=use_blooms)

        return func.HttpResponse(
            body=json.dumps(flashcards, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.exception("Error in flashcard generator function")
        return func.HttpResponse(str(e), status_code=500)