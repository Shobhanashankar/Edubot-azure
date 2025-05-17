import os
import re
import nltk
from transformers import pipeline
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

# Force download of 'punkt' model (sentence tokenizer)
nltk.download('punkt')

def clean_text(text):
    # Remove extra whitespace and page numbers like "Page 12"
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page\s*\d+[:.]?', '', text, flags=re.IGNORECASE)
    return text.strip()

def chunk_text(text, max_chunk_size=1000):
    # Use explicit PunktSentenceTokenizer to avoid sent_tokenize issues
    punkt_param = PunktParameters()
    tokenizer = PunktSentenceTokenizer(punkt_param)
    sentences = tokenizer.tokenize(text)
    
    chunks = []
    current_chunk = ""

    for sent in sentences:
        # +1 for space
        if len(current_chunk) + len(sent) + 1 <= max_chunk_size:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def generate_summary(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    cleaned_text = clean_text(text)
    chunks = chunk_text(cleaned_text)

    summaries = []
    for chunk in chunks:
        max_len = min(150, max(30, len(chunk)//5))
        min_len = min(40, max_len//2)
        result = summarizer(chunk, max_length=max_len, min_length=min_len, do_sample=False)
        summaries.append(result[0]['summary_text'])

    combined_summary = " ".join(summaries)
    return combined_summary.strip()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Summarize input text file")
    parser.add_argument("input_file", help="Path to input .txt file")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Input file does not exist: {args.input_file}")
        exit(1)

    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    summary = generate_summary(text)
    output_file = args.input_file.replace(".txt", "_summary.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\n✅ Summary written to: {output_file}")