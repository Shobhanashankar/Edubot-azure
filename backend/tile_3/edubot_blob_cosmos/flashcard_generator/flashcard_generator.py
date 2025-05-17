"""
flashcard_generator.py - Generate flashcards using keywords, similarity & summary
Usage:
    python flashcard_generator.py summary_file.txt
"""

import os
import sys
import json
import re
import numpy as np
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from transformers import pipeline

def basic_sentence_split(text):
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page\s*\d+[:.]?', '', text, flags=re.IGNORECASE)
    return text.strip()

def chunk_text(text, max_chunk_size=1000):
    sentences = basic_sentence_split(text)
    chunks = []
    current_chunk = ""
    for sent in sentences:
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
        input_len = len(chunk.split())
        max_len = min(150, max(30, input_len))
        min_len = min(40, max_len // 2)
        result = summarizer(chunk, max_length=max_len, min_length=min_len, do_sample=False)
        summaries.append(result[0]['summary_text'])

    return " ".join(summaries).strip()

def extract_keywords(text, max_keywords=10):
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    stopwords = set("""
        i me my myself we our ours ourselves you your yours yourself yourselves he him his himself
        she her hers herself it its itself they them their theirs themselves what which who whom this
        that these those am is are was were be been being have has had having do does did doing a an
        the and but if or because as until while of at by for with about against between into through
        during before after above below to from up down in out on off over under again further then
        once here there when where why how all any both each few more most other some such no nor not
        only own same so than too very s t can will just don should now
    """.split())

    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    vectorizer = CountVectorizer().fit([text])
    word_counts = vectorizer.transform([text]).toarray().flatten()
    keywords = np.array(vectorizer.get_feature_names_out())[np.argsort(-word_counts)]
    return keywords[:max_keywords].tolist()

def is_similar(existing, new_sent, model, threshold=0.8):
    if not existing:
        return False
    new_vec = model.encode([new_sent])
    existing_vecs = model.encode(existing)
    sims = cosine_similarity(new_vec, existing_vecs)
    return np.max(sims) > threshold

def generate_questions_from_keywords(keywords):
    templates = [
        "What is {}?",
        "Explain the concept of {}.",
        "Why is {} important?",
        "How does {} work?",
    ]
    questions = []
    for i, kw in enumerate(keywords):
        template = templates[i % len(templates)]
        questions.append(template.format(kw))
    return questions

def generate_blooms_questions(sentence):
    return [
        f"What can you infer from: '{sentence}'?",
        f"Can you explain: '{sentence}'?",
        f"How would you evaluate this statement: '{sentence}'?",
    ]

def generate_flashcards(text, summary, use_blooms=False):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

    keywords = extract_keywords(summary)
    keyword_questions = generate_questions_from_keywords(keywords)

    flashcards = []
    used_sentences = []

    for q in keyword_questions:
        try:
            answer = qa_pipeline(question=q, context=text)
            if answer["score"] > 0.3 and answer["answer"].strip():
                flashcards.append({
                    "question": q,
                    "answer": answer["answer"].strip()
                })
        except Exception:
            continue

    summary_sentences = basic_sentence_split(summary)
    for sent in summary_sentences:
        if is_similar(used_sentences, sent, model):
            continue
        used_sentences.append(sent)
        if use_blooms:
            questions = generate_blooms_questions(sent)
            for q in questions:
                try:
                    answer = qa_pipeline(question=q, context=text)
                    if answer["score"] > 0.3 and answer["answer"].strip():
                        flashcards.append({
                            "question": q,
                            "answer": answer["answer"].strip()
                        })
                except Exception:
                    continue

    return flashcards

def main():
    if len(sys.argv) < 2:
        print("Usage: python flashcard_generator.py <input_text_file>")
        return

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    print("🔍 Generating summary...")
    summary = generate_summary(text)

    print("🧠 Generating flashcards...")
    flashcards = generate_flashcards(text, summary, use_blooms=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_file = f"{base_name}_flashcards.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(flashcards, f, indent=2, ensure_ascii=False)

    print(f"✅ Flashcards saved to: {out_file}")

if __name__ == "__main__":
    main()
