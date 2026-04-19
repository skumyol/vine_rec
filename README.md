# Wine Photo Verification System

> **VinoBuzz Internship Assignment** — Automated Wine Photo Sourcing Accuracy Challenge. Target: **90% accuracy on 10 test SKUs** (baseline was 50%).

A verification-first wine photo sourcing pipeline that parses each SKU into structured wine identity fields, retrieves web image candidates via Bing image search (Playwright WebKit), filters them through OpenCV-based quality checks, extracts label text with OCR, and verifies exact bottle identity using VLM analysis (Gemini + Qwen-VL).

## Philosophy: Prefer "No Image" Over Wrong Image

The system is designed specifically to avoid false positives. If no candidate meets the strict acceptance threshold, the system returns "No Image" rather than risking an incorrect bottle photo.

## System Architecture

### Five-Layer Pipeline

1. **Input & Normalization**: Parses wine names into structured fields (producer, appellation, vineyard, vintage, classification)
2. **Search & Collection**: Uses **Playwright with WebKit** to search Bing Images. Converts thumbnails to full-size images (800x1000) for better OCR quality.
3. **Fast Image Screening**: OpenCV-based filtering (single bottle, upright, clean background, no glare)
4. **Verification**: OCR + text matching + VLM analysis (Gemini + Qwen-VL)
5. **Decision Engine**: Scores candidates and returns verified image or "No Image"

### Verification Modes

- `hybrid_fast` *(default)*: OpenCV → OCR → One VLM (Gemini)
- `hybrid_strict`: OpenCV → OCR → Both Gemini + Qwen (recommended for demos)
- `gemini`: OpenCV → OCR → Gemini only
- `qwen_vl`: OpenCV → OCR → Qwen-VL only
- `opencv_only`: Debug mode with just image quality checks

Gemini can run against the native Gemini API or OpenRouter. Qwen runs via OpenRouter.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm (frontend), `uv` (backend, per project convention)
- API key: **OpenRouter** (covers Gemini + Qwen-VL) or native Gemini/Qwen keys

### Environment Setup

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your API keys
vim .env
```

Required environment variables:

```
# Recommended: single OpenRouter key routes both Gemini and Qwen-VL
OPENROUTER_API_KEY=your_openrouter_key

# Optional native keys (used when valid, otherwise falls back to OpenRouter)
GEMINI_API_KEY=your_gemini_key
QWEN_API_KEY=your_qwen_key
```

Other config (see `backend/app/core/config.py`):

```
DEFAULT_ANALYZER_MODE=hybrid_fast
PASS_THRESHOLD=25
REVIEW_THRESHOLD=15
GEMINI_MODEL=gemini-1.5-flash  # or google/gemini-2.0-flash-001 via OpenRouter
```

### Development

```bash
# Run development servers (backend + frontend)
./run_dev.sh

# Check whether dev servers are running
./run_prod.sh --check
```

This starts:

- Backend API at http://localhost:8001
- Frontend at http://localhost:3001
- API docs at http://localhost:8001/docs

### Frontend Batch UI

Visit http://localhost:3001/batch. Click **Load Test Set (10)** to populate the 10 assignment SKUs, then **Analyze All 10 Wines**. The UI submits an async job and polls progress; each SKU takes ~90–150s.

The results table shows PASS / REVIEW / FAIL / NO_IMAGE verdicts plus an overall accuracy percentage (PASS + REVIEW counted as verified).

### Production Deployment

```bash
# Deploy with Docker
./run_prod.sh
```

## API Endpoints

### Single Wine Analysis (sync)

```bash
POST /api/analyze/
{
  "wine_name": "Domaine Arlaud Morey-St-Denis Monts Luisants 1er Cru",
  "vintage": "2019",
  "format": "750ml",
  "region": "Burgundy",
  "analyzer_mode": "hybrid_fast"
}
```

### Batch Analysis (async jobs)

Long-running batch requests use the async jobs API to avoid HTTP timeouts:

```bash
# 1. Create job (returns immediately)
POST /api/jobs/batch
{
  "wines": [ { "wine_name": "...", "vintage": "2017" }, ... ],
  "analyzer_mode": "hybrid_fast"
}
# -> { "job_id": "abc12345", "status": "pending", ... }

# 2. Poll for progress + results
GET /api/jobs/{job_id}
# -> { status, total_wines, completed_wines, results: [...], errors: [...] }
```

A sync batch endpoint (`POST /api/analyze/batch`) is also available for small batches.

### Response Shape

```json
{
  "input": { ... },
  "parsed_sku": {
    "producer": "Domaine Arlaud",
    "appellation": "Morey-St-Denis",
    "vineyard": "Monts Luisants",
    "classification": "1er Cru"
  },
  "selected_image_url": "https://...",
  "confidence": 92,
  "verdict": "PASS",  // PASS | REVIEW | FAIL | NO_IMAGE
  "reason": "...",
  "top_candidates": [ ... ]
}
```

### Other Endpoints

- `GET /api/health` — service health + threshold config
- `GET /api/analyzer-modes` — list of available analyzer modes
- `GET /api/results/` — paginated history (SQLite-backed)
- `GET /api/results/{run_id}` — detail for a single run
- `GET /api/results/export/csv` — CSV export
- `GET /api/wines/` — VinoBuzz wine catalogue helpers

## Project Structure

```
vine_rec/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── api/                   # routes_analyze, routes_jobs, routes_results,
│   │   │                          #   routes_wines, routes_health
│   │   ├── core/                  # config, constants (AnalyzerMode, Verdict)
│   │   ├── db/                    # SQLAlchemy models for run history
│   │   ├── models/                # Pydantic: sku, candidate, result, job
│   │   └── services/              # pipeline, retriever_playwright, search_service,
│   │                              #   downloader, opencv_analyzer, ocr_service,
│   │                              #   gemini_verifier, qwen_verifier, scorer,
│   │                              #   parser, query_builder, job_manager
│   ├── test_assignment_skus.py    # 10 SKU evaluator (writes data/results/*.json)
│   ├── test_single_sku.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                       # Next.js app (analyze page, /batch page)
│   ├── components/                # BatchResultsTable, etc.
│   ├── lib/                       # api.ts (createBatchJob, pollBatchJob, ...)
│   └── package.json
├── data/                          # images/, cache/, results/ (runtime artifacts)
├── nginx/                         # Reverse proxy config for prod
├── docker-compose.yml
├── run_dev.sh                     # Local dev (ports 8001 / 3001)
├── run_prod.sh                    # Docker prod (supports --check)
├── assignment.md                  # Original VinoBuzz brief
└── README.md
```

## Scoring System

### Score Weights

- Image Quality (OpenCV): 20%
- Text Verification (OCR + Matching): 40%
- VLM Verification (Gemini / Qwen): 40%

### Verdict Thresholds

Defined in `backend/app/services/scorer.py` (`pass_threshold=25`, `review_threshold=15`):

- **PASS**: 25+ points (confident match)
- **REVIEW**: 15–24 points (borderline, human verification recommended)
- **FAIL**: <15 points (clear mismatch)
- **NO_IMAGE**: No candidate cleared the minimum bar

### Hard Fail Rules

Implemented in `ScoringEngine` (see `scorer.py`) — currently tuned to be informative rather than disqualifying:

- Producer / appellation / vineyard mismatches penalize the score but don't auto-fail
- OpenCV warnings (multi-bottle, watermark, blur) reduce score but remain visible
- VLM disagreement drops confidence but can still reach REVIEW

This matches the assignment philosophy of preferring an honest "No Image" over a wrong image.

## Current Status & Limitations

### What works today

- **SKU parsing** — extracts producer, appellation, vineyard, vintage, classification (`parser.py`)
- **Query building** — de-duplicates appellation/vineyard tokens (`query_builder.py`)
- **Image search** — Bing via Playwright **WebKit** (Chromium was crashing on this Mac)
- **Thumbnail upscaling** — rewrites Bing `w=42&h=42` thumbnails to `w=800&h=1000` for usable OCR input
- **OpenCV screening** — rejects tiny / blurry images before download cost
- **OCR** — EasyOCR with confidence filtering (GPU via MPS when available)
- **VLM** — Gemini verifier auto-routes to OpenRouter when the native key is missing / placeholder; Qwen verifier always via OpenRouter
- **Async batch jobs** — non-blocking `/api/jobs/batch` + `GET /api/jobs/{id}` with progress, used by the `/batch` UI
- **Persistence** — SQLite run history + JSON exports under `data/results/`

### Known challenges

- **Image source quality** — Bing often returns generic appellation wines instead of the specific producer (e.g. "Château Fonroque" → other Saint-Émilions). This is the dominant cause of NO_IMAGE on niche SKUs.
- **Niche wines** — small producers and off-vintages have very sparse web coverage
- **Latency** — ~90–150s per SKU end to end; the Bing scroll + VLM round-trip dominates
- **VLM cost** — `hybrid_strict` doubles VLM calls (Gemini + Qwen)

### Target accuracy

Goal: **≥90% of the 10 test SKUs verified** (PASS or REVIEW).
Current: pipeline runs end-to-end; image retrieval quality is the limiting factor for the hardest SKUs.

## Testing

### Single SKU

```bash
cd backend
source .venv/bin/activate
python test_single_sku.py
```

### 10-SKU Assignment Run

```bash
cd backend
source .venv/bin/activate
python test_assignment_skus.py
```

Results are written to `data/results/test_results_<timestamp>.json` and summarized in the console (PASS / REVIEW / FAIL / NO_IMAGE distribution, per-SKU timing, overall accuracy vs. the 90% target).

The same 10 SKUs are available in the frontend at `/batch` via **Load Test Set (10)**.

## Assignment Reference

See [`assignment.md`](./assignment.md) for the original VinoBuzz brief. Test SKUs wired into `test_assignment_skus.py` and the `/batch` UI:

1. Domaine Rossignol-Trapet Latricieres-Chambertin Grand Cru (2017, Burgundy, *Hard*)
2. Domaine Arlaud Morey-St-Denis 'Monts Luisants' 1er Cru (2019, Burgundy, *Hard*)
3. Domaine Taupenot-Merme Charmes-Chambertin Grand Cru (2018, Burgundy, *Hard*)
4. Château Fonroque Saint-Émilion Grand Cru Classé (2016, Bordeaux, *Medium*)
5. Eric Rodez Cuvée des Crayeres Blanc de Noirs (NV, Champagne, *Medium*)
6. Domaine du Tunnel Cornas 'Vin Noir' (2018, Northern Rhône, *Hard*)
7. Poderi Colla Barolo 'Bussia Dardi Le Rose' (2016, Piedmont, *Medium*)
8. Arnot-Roberts Trousseau Gris Watson Ranch (2020, Sonoma, *Very Hard*)
9. Brokenwood Graveyard Vineyard Shiraz (2015, Hunter Valley, *Medium*)
10. Domaine Weinbach Riesling 'Clos des Capucins' Vendanges Tardives (2017, Alsace, *Hard*)

## License

MIT
