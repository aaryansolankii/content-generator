# Instagram AI Content Strategy Engine (FastAPI Backend)

Production-oriented FastAPI backend for:
1. Optional competitor analysis
2. Idea generation (`/generate-ideas`, fixed to 5 ideas)
3. Niche-based expansion + calendar generation (`/generate-calendar`)
4. Suggestion-based intent endpoint (`/suggest-ideas`)
5. On-demand script generation per selected calendar day

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
- `POST /api/v1/suggest-ideas`
- `POST /api/v1/generate-script`
- `GET /health`

## Example cURL Requests

### 1) Generate Ideas (with optional competitor URL)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-ideas" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "Personal Finance for Gen Z",
    "target_audience": "Indian college students and first-job professionals",
    "language": "Hinglish",
    "start_date": "2026-03-10",
    "competitor_url": "https://example.com"
  }'
```

### 2) Suggest Ideas From Search Intent

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/suggest-ideas" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want to create reels about salary budgeting for freshers",
    "duration_days": 30
  }'
```

### 3) Generate Calendar (niche -> base ideas -> expanded ideas -> schedule)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "Personal Finance for Gen Z",
    "target_audience": "Indian college students and first-job professionals",
    "duration_days": 30,
    "language": "English",
    "start_date": "2026-03-10",
    "competitor_url": null
  }'
```

### 4) Generate Script (for selected calendar day)

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
- Calendar endpoint generates 5 base ideas from niche, expands to requested days, then schedules.
- `/generate-ideas` is fixed to exactly 5 base ideas.
- `/generate-ideas` does not include `duration_days` or `number_of_ideas` in input.
- `/suggest-ideas` infers missing context and returns follow-up requirement questions plus query suggestions.
- Calendar response also includes `calendar_sheet` rows aligned to spreadsheet columns:
  `Post Date`, `Day`, `Post Format`, `Theme`, `Hook`, `Key Visual Direction`, `Primary CTA`, `Suggested Hashtags`.
- For large durations, backend auto-processes expansion and calendar in batches for better reliability.
- Script generation is on-demand and independent per request.
- Gemini responses are JSON-validated. If invalid, service retries once.
- Keys are loaded from environment variables; no hardcoded credentials.
