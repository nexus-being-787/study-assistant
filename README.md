<div align="center">

# 📚 Study Assistant

### A Local AI-Powered Study Assistant built with **llama.cpp**, **ChromaDB**, and **RAG**

Generate detailed explanations, summaries, quizzes, flashcards, and beautiful study sheets — completely **offline** using your own local LLM.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![llama.cpp](https://img.shields.io/badge/LLM-llama.cpp-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![License](https://img.shields.io/badge/Status-Active-success)

</div>

---

# ✨ Features

- 🧠 **Local AI** — Runs completely offline using `llama.cpp`
- 📖 **RAG (Retrieval-Augmented Generation)** with ChromaDB
- 📄 Import PDF study materials
- 💬 Ask questions from your notes
- 📝 Generate detailed explanations
- 📚 Create summaries
- 🎯 Generate quizzes
- 🗂 Create flashcards
- 🌐 Export beautiful HTML study sheets
- 📄 Export PDF using Playwright
- ⚡ CLI-first architecture

---

# 🏗 Architecture

```
                 ┌─────────────────────┐
                 │    PDF Documents    │
                 └──────────┬──────────┘
                            │
                    Document Loader
                            │
                            ▼
                     Text Chunking
                            │
                            ▼
                    Embedding Model
                            │
                            ▼
                       ChromaDB
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
   Similarity Search                     Retrieved Chunks
                                                │
                                                ▼
                                           Prompt Builder
                                                │
                                                ▼
                                           llama.cpp LLM
                                                │
                                                ▼
                         HTML / Markdown / PDF / Study Notes
```

---

# 📂 Project Structure

```text
study-assistant/
├── src/
│   └── study_assistant/
│       ├── cli/
│       ├── llm/
│       ├── embeddings/
│       ├── ingestion/
│       ├── rag/
│       ├── renderer/
│       └── vectorstore/
│
├── data/
│   ├── docs/
│   └── chroma/
│
├── models/
├── output/
├── pyproject.toml
└── README.md
```

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/nexus-being-787/study-assistant.git

cd study-assistant
```

Install dependencies

```bash
uv sync
```

Install Playwright

```bash
uv run playwright install chromium
```

---

# 📥 Models

Place your GGUF model inside:

```text
models/
```

Example:

```
models/
└── Phi-4-mini-instruct.gguf
```

---

# 📄 Add Documents

Copy your study materials into

```text
data/docs/
```

Supported formats include:

- PDF
- TXT

*(More formats coming soon.)*

---

# ⚡ Usage

## Index Documents

```bash
uv run study ingest
```

---

## Ask Questions

```bash
uv run study ask "Explain CPU registers" --mode explain
```

---

## Generate Summary

```bash
uv run study ask "Operating System" --mode summarize
```

---

## Generate Quiz

```bash
uv run study ask "Computer Networks" --mode quiz
```

---

## Flashcards

```bash
uv run study ask "DBMS" --mode flashcard --save
```

---

## Generate Notes

```bash
uv run study ask "Artificial Intelligence" --mode notes --save --pdf
```

---

## Project Info

```bash
uv run study info
```

---

# 🧠 How It Works

1. Documents are loaded.
2. Text is split into chunks.
3. Chunks are converted into embeddings.
4. Embeddings are stored inside ChromaDB.
5. Your question is embedded.
6. Similar chunks are retrieved.
7. Retrieved context is sent to the local LLM.
8. The answer is rendered as study material.

---

# 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| LLM | llama.cpp |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| RAG | LangChain |
| CLI | Typer |
| Templates | Jinja2 |
| HTML Rendering | Playwright |

---

# 🗺 Roadmap

## Current

- [x] Local LLM integration
- [x] PDF ingestion
- [x] ChromaDB
- [x] RAG pipeline
- [x] HTML renderer
- [x] PDF export
- [x] CLI interface

---

## Planned

- [ ] Direct LLM Chat Mode
- [ ] PNG study sheet export
- [ ] Mermaid diagrams
- [ ] Mind maps
- [ ] Multi-document search
- [ ] Better retrieval (Reranker)
- [ ] OCR support
- [ ] n8n automation
- [ ] Web UI
- [ ] Image generation for notes

---

# 💡 Vision

The goal of this project is to build a fully local AI study companion that can transform textbooks, notes, and question banks into clear, visually appealing study material while keeping your data private.

---

# 🤝 Contributing

Contributions, suggestions, and feature requests are welcome!

Feel free to open an issue or submit a pull request.

---

# 📜 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ using Python, llama.cpp, ChromaDB, and open-source AI.**

⭐ If you find this project useful, consider giving it a star!

</div>