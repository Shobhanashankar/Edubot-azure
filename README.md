# 📚 EduBotAI+ — Your AI-Powered Study Companion 🚀

EduBotAI+ is an AI-powered smart learning assistant that transforms how students engage with study material. It supports PDFs, images, handwritten notes, and slides—using Azure's services to extract content. Leveraging NLP techniques, it performs **text extraction**,**grammar correction**, **summarization**, **translation**, and **flashcard generation**. With added voice-based input/output, EduBotAI+ simplifies complex concepts into interactive, easy-to-understand formats—making learning faster and more personalized. l

---

## ✨ Features

### 📥 Upload & Choose Operation

Users can upload **PDFs, images, or audio**, and choose from:
- 📝 **Text Converter** – Extracts text from documents and images using OCR.
- 🧠 **Summary Creator** – Cleans and summarizes large texts for quick understanding.
- 🎙️ **Voice Translator** – Converts speech to text, translates, and generates a subtitle video or audio.

---

### 🎤 Voice Input → Text Conversion

- **Uses**: Azure Speech-to-Text
- **Supports**: Direct microphone input or uploaded `.wav/.mp3` files
- **Output**: Recognized transcript saved as `voice_transcript.txt`

---

### 🔁 Flashcard Generator

- Converts summarized content or notes into **Q&A flashcards**
- Extracts key concepts using:
  - Keyword analysis
  - Sentence similarity
  - Bloom’s taxonomy (optional)
- **Output format**: Readable list and downloadable `.txt` or `.json`

---

### 🗣️ Text-to-Speech Translator with Video

- **Input**: User-typed or extracted text
- **Language Options**:
  - English 🇬🇧
  - Tamil 🇮🇳
  - Hindi 🇮🇳
  - Telugu 🇮🇳
- **Output**:
  - 🎧 Audio (.mp3)
  - 🎞️ MP4 video with:
    - Subtitles in selected language
    - Custom or default background image

---

## 🧠 Technologies Used

### 🔧 Backend Stack
- **Python**
- **Azure Services**:
  - Azure Speech Service (STT + TTS) – Free Tier
  - Azure Computer Vision OCR – Free Tier
  - Azure Blob Storage – For storing processed files
  - Azure Cosmos DB – For storing metadata and logs
  - Azure Translator - For translating text to speech - Free Tier

### 🌐 Frontend Stack
- **HTML/CSS/JavaScript**
- Responsive UI for uploads, operations, and results display

---

## ✅ How It Works – Workflow Breakdown

### Step 1: Voice Input
- Users speak or upload an audio file
- Azure STT converts speech to text
- Saved as transcript for next steps

### Step 2: OCR (Text Extraction)
- PDFs, scanned images, and handwritten notes are processed
- Azure OCR extracts raw text from uploaded files

### Step 3: Text Cleaning & Summarization
- Removes noise (special characters, formatting issues)
- Outputs clean paragraphs
- Summarization done using OpenAI or rule-based logic

### Step 4: Flashcard Generation
- Smart Q&A generated from clean text
- Exportable for revision or quiz practice

### Step 5: TTS and Subtitle Video
- User text is converted to speech (TTS)
- Subtitle video generated with selected language and image
- Stored in Azure Blob Storage for later access/download

---

## 📁 File Storage & Output Management

All outputs including:
- Cleaned text
- Summaries
- Flashcards (.txt/.json)
- Transcripts
- MP4 videos with subtitles

...are automatically **uploaded and organized** in **Azure Blob Storage**, with metadata tracked in **Azure Cosmos DB** for easy access and audit.

---

## 🧪 Example Use Case

> A student uploads a PDF chapter and selects “Summary Creator” → EduBotAI+ extracts and cleans the text, summarizes it, and generates flashcards. They can also listen to the summary in Hindi or generate a video with Tamil subtitles for revision.

---
## 🚀 Future Enhancements (Student-Focused)

🔎 1. Semantic Search on Summarized/Corrected Content
Enable *intelligent search* using vector embeddings (e.g., `SentenceTransformers`):
- 🔍 Search similar summaries based on meaning, not just keywords
- ❓ Ask questions across multiple documents
- 🧠 Smart retrieval: “Find notes where cybersecurity attacks were mentioned”

🧠 2. LLM-Powered Summary QA (Question-Answering)
Integrate with LLMs like OpenAI GPT or Anthropic Claude for enhanced interaction:
- 📝 "Summarize this. Now give 3 bullet points and a call to action."
- ❓ Ask clarifying questions on the summary
- ✅ Improve summary coherence and factual accuracy

🧪 3. Multimodal Input Handling
Extend input types beyond PDF/Image/PPTX:
- 🎧 **Audio Support (MP3, WAV):**
  - Transcribe using Whisper / Google STT
  - Clean and summarize the transcript
- 📹 **YouTube or Video Link Support:**
  - Frame-by-frame OCR for visual content
  - Summarize lecture visuals/texts

---
## ⚙️ Installation
- Clone the repository
- Install the virtual environment and dependencies
- Train the model and run the flask Application

---
## 👥 Collaborators

| Name              | GitHub Username |
| ----------------- | --------------- |
| **Shobhana S**    | @Shobhanashankar|
| **Gautham R**     | @gautham-here   |
| **Sri Ranjana C** | @ @sriranjanac  |



