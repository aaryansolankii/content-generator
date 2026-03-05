# Instagram AI Content Strategy Engine (FastAPI Backend)

Production-oriented FastAPI backend for:
1. Optional competitor analysis
2. Idea generation (`/generate-ideas`)
3. Combined expansion + calendar generation (`/generate-calendar`)
4. On-demand script generation per selected calendar day

## Project Structure

```text
app/
  main.py
  config.py
  routes/
  services/
  schemas/
  utils/
requirements.txt
.env.example
```

## Setup

1. Create virtual environment:

```bash
python -m venv .venv
```

2. Activate environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

5. Edit `.env` and set `GEMINI_API_KEY`.

6. Run API:

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `POST /api/v1/generate-ideas`
- `POST /api/v1/generate-calendar`
- `POST /api/v1/generate-script`
- `GET /health`
- `GET /api/v1/health`

## Example cURL Requests

### 1) Generate Ideas (with optional competitor URL)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-ideas" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "Personal Finance for Gen Z",
    "target_audience": "Indian college students and first-job professionals",
    "number_of_ideas": 7,
    "duration_days": 21,
    "language": "Hinglish",
    "start_date": "2026-03-10",
    "competitor_url": "https://example.com"
  }'
```

### 2) Generate Calendar (expands selected ideas + schedules calendar)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_days": 30,
    "language": "English",
    "start_date": "2026-03-10",
    "selected_ideas": [
      {
        "idea_id": "3dcb5bb8-7f13-4e4c-bcc0-0f5a30d2d331",
        "title": "3 Money Mistakes Freshers Make",
        "format": "Reel",
        "pillar": "Education",
        "description": "Quick breakdown of common salary-handling mistakes and fixes."
      },
      {
        "idea_id": "e60f0f33-a081-4726-94ec-4b8b74e7087f",
        "title": "Budgeting Framework for 20-Somethings",
        "format": "Carousel",
        "pillar": "Authority",
        "description": "Step-by-step budgeting system with an actionable template."
      }
    ]
  }'
```

### 3) Generate Script (for selected calendar day)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "idea_id": "3dcb5bb8-7f13-4e4c-bcc0-0f5a30d2d331",
    "title": "3 Money Mistakes Freshers Make",
    "format": "Reel",
    "pillar": "Education",
    "language": "Hindi",
    "angle": "First salary month"
  }'
```

## Notes

- Calendar mapping is LLM-driven (no random Python distribution).
- Language can be selected per request (English, Hindi, Hinglish, Tamil, etc.).
- Calendar endpoint internally expands selected ideas before scheduling.
- Calendar response also includes `calendar_sheet` rows aligned to spreadsheet columns:
  `Post Date`, `Day`, `Post Format`, `Theme`, `Hook`, `Key Visual Direction`, `Primary CTA`, `Suggested Hashtags`.
- For large durations, backend auto-processes expansion and calendar in batches for better reliability.
- Script generation is on-demand and independent per request.
- Gemini responses are JSON-validated. If invalid, service retries once.
- Keys are loaded from environment variables; no hardcoded credentials.
