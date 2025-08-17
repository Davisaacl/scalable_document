# Scalable Document Analysis System (FastAPI + FAISS + SBERT)

A pipeline ready to use that can process documents (PDF/DOCX/JSON), extract text, generate **embeddings** with Sentence-Transformers, index them in **FAISS**, and expose **semantic search** over an HTTP API. Includes **Docker + docker-compose**, optional **NER** (spaCy) and a simple **classifier**.

## ✨ Features

- ✅ Input formats: **PDF**, **DOCX**, **JSON** (JSON reader is BOM-tolerant).
- ⚡ Parallel ingestion (`ThreadPoolExecutor`).
- 🔎 **Semantic search** with SBERT embeddings + FAISS (cosine via inner product on normalized vectors).
- 🗂️ Persistence: **DuckDB** (metadata) and FAISS index under `./data`.
- 🧠 Optional: **NER** (spaCy) and **Classifier** (TF-IDF + LinearSVC).
- 📦 **Dockerized** for consistent local runs.

## 📁 Project Structure
```text
app/
├─ api/v1/
│  ├─ routes_documents.py  # /documents/upload
│  ├─ routes_search.py     # /search
│  └─ routes_models.py     # /models/ner, /models/classifier/*
├─ core/
│  ├─ config.py            # settings (pydantic-settings)
│  └─ logging_conf.py      # structured JSON logging
├─ pipeline/
│  ├─ parsers.py           # PDF/DOCX/JSON → text blocks (extension-based)
│  ├─ embedder.py          # texts → embeddings (single-model SBERT)
│  ├─ indexer.py           # FAISS (FlatIP; cosine with normalized vectors)
│  ├─ storage.py           # DuckDB (documents/blocks)
│  └─ document_models.py
├─ workers/
│  └─ tasks.py             # ingestion orchestration
└─ main.py                 # FastAPI app
docker/
└─ Dockerfile
docker-compose.yml
requirements.txt
.env.example
```

---

## 🚀 Quickstart (Docker recommended)

### Prereqs
- **Docker Desktop** running (WSL2 on Windows).
- Port **8000** available (or change the mapping in compose).

### Steps
```bash
# 1) Clone and enter
git clone <your-repo>.git
cd <your-repo>

# 2) (optional) local env
cp .env.example .env

# 3) Build and run
docker compose up --build
# or detached:
# docker compose up -d --build
```

Open:
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

The first search may take a bit while models download. They’re cached under `./.hf_cache`.

### Sample
#### 1) Create sample files

Windows (PowerShell):
```powershell
# JSON (BOM-free)
python -c "open('sample.json','w',encoding='utf-8').write('{\"name\":\"Demo\",\"items\":[{\"sku\":\"A1\",\"qty\":2}]}')"

# DOCX with 2 paragraphs
python -c "from docx import Document; d=Document(); d.add_paragraph('Lease contract'); d.add_paragraph('General clauses'); d.save('sample.docx')"
```
#### 2) Upload documents
Swagger → `POST /documents/upload` → “Try it out” → select `sample.json` and `sample.docx`.

With command line PowerShell:
```powershell
curl.exe -X POST "http://localhost:8000/documents/upload" -F "files=@sample.json" -F "files=@sample.docx"
```

Expected:
```json
{
  "saved": ["/app/data/sample.docx", "/app/data/sample.json"],
  "ingested_docs": 2,
  "blocks_indexed": 3,
  "errors": []
}
```

#### 3) Semantic search
```powershell
curl.exe "http://localhost:8000/search?q=contract%20termination&k=5"
```

### Endpoints

1. ```GET /health``` — service status.
2. ```POST /documents/upload``` — multipart upload; triggers parse → persist → embed → index.
3. ```GET /search``` — query params:
   - ```q``` (str, required): query text
   - ```k``` (int, optional): top-k (default 5)
4. ```POST /models/ner``` — body ```{"text":"..."}``` → entities (label + offsets) via spaCy.
5. ```POST /models/classifier/train``` — body ```{"texts":[...],"labels":[...]}``` → trains TF-IDF + LinearSVC and persists it.
6. ```POST /models/classifier/predict``` — body ```{"texts":[...]}``` → label + (calibrated) scores per class.

### Configuration

```.env.example```

```ini
ENV=dev
LOG_LEVEL=INFO
DATA_DIR=./data
INDEX_DIR=./data/index
DB_PATH=./data/meta.duckdb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Change **EMBEDDING_MODEL**, then re-ingest (or clear ```./data```) to rebuild the index.

DuckDB + FAISS live under ```./data``` (mounted as a volume by compose).

### Local development (without Docker)

Use either Docker or a local venv — avoid running both on port 8000.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m uvicorn app.main:app --reload
```

### Tests

With Docker

```bash
docker compose exec api python -m pytest -q
```
Locally

```bash
pytest -q
```

### Troubleshooting

Can’t open ```http://localhost:8000/docs```

- Ensure Docker Desktop shows “Engine running”.
- ```docker compose up -d --build```
- Tail logs: ```docker compose logs -f api```

```Field required: files``` when uploading
- PowerShell ignored ```-F``` due to line breaks. Use ```curl.exe``` on a single line (no ```^```).

```.docx``` seen as ```application/octet-stream```
- Parser uses **file extension** mapping, not OS MIME DB. Ensure you’re on the extension-based ```parsers.py``` (included).

**JSON with BOM**
Reader uses ```encoding="utf-8-sig"``` (BOM-tolerant). Prefer writing JSON without BOM.

**Pydantic v2** (```BaseSettings``` moved)
- This repo uses ```pydantic-settings```. Install from ```requirements.txt```.

**Port 8000 busy**
- Change compose to ```ports: ["8080:8000"]``` and open ```http://localhost:8080```.

**Reset everything (DB + index + cache)** 
```bash
docker compose down -v
docker compose up -d --build
```

### Design Highlights

1. Embeddings: ```all-MiniLM-L6-v2``` (384-d), fast and strong baseline.
2. Index: FAISS ```IndexFlatIP``` using normalized vectors for cosine similarity.
3. Persistence: DuckDB (single file; easy swap to Postgres).
4. Parsers: pdfplumber (PDF), python-docx (DOCX), JSON flattener (BOM-tolerant).
5. Parallel ingestion: ```ThreadPoolExecutor```.
6. Structured logging: JSON logs.

## 1) Upload Documents
Create sample files (optional) in Windows (PowerShell)
```powershell
python -c "open('sample.json','w',encoding='utf-8').write('{\"name\":\"Demo\",\"items\":[{\"sku\":\"A1\",\"qty\":2}]}')"
python -c "from docx import Document; d=Document(); d.add_paragraph('Lease contract'); d.add_paragraph('General clauses'); d.save('sample.docx')"
```
Upload (multipart/form-data)
```powershell
curl.exe -X POST "http://localhost:8000/documents/upload" -F "files=@sample.json" -F "files=@sample.docx"
```
Expected:
```json
{
  "saved": ["/app/data/sample.docx", "/app/data/sample.json"],
  "ingested_docs": 2,
  "blocks_indexed": 3,
  "errors": []
}
```
## 2) Semantic Search
Windows
```powershell
curl.exe "http://localhost:8000/search?q=contract%20termination&k=5"
```
## 3) NER
Windows
```powershell
curl.exe -X POST "http://localhost:8000/models/ner" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Apple acquired Beats for $3B in 2014 in California.\"}"
```
## 4) Classifier Train & Predict (Optional)
Windows
1. Train
```powershell
curl.exe -X POST "http://localhost:8000/models/classifier/train" ^
  -H "Content-Type: application/json" ^
  -d "{\"texts\":[\"Lease contract terms\",\"Consulting invoice\"],\"labels\":[\"legal\",\"finance\"]}"
```
2. Predict
```powershell
curl.exe -X POST "http://localhost:8000/models/classifier/predict" ^
  -H "Content-Type: application/json" ^
  -d "{\"texts\":[\"Termination clause of the lease\",\"Payment receipt for July\"]}"
```
## 5) Admin/Ops
1. Logs
```bash
docker compose logs -f api
```
2. Check containers
```bash
docker compose ps
```
3. Open shell in the container
```bash
docker compose exec api bash
```
4. Run tests (in container)
```bash
docker compose exec api python -m pytest -q
```
1. Reset everything /DB + index + cahe)
```bash
docker compose down -v
docker compose up -d --build
``` 
