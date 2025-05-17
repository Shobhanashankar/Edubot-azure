import json
import azure.functions as func
from edubot_pipeline.summarizer.summarizer import generate_summary

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
    except Exception:
        return func.HttpResponse("Invalid JSON input", status_code=400)

    text = data.get("text")
    if not text:
        return func.HttpResponse("Missing 'text' field", status_code=400)

    try:
        # Call your existing summary generation code
        summary = generate_summary(text)
        result = {"summary": summary}
        return func.HttpResponse(json.dumps(result), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
