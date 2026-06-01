# AI Research Agent 🤖

An AI-powered competitive intelligence agent built on Google Cloud Platform. Give it a company name — get back a structured research brief powered by Claude + web search.

**Live demo:** `https://research-agent-XXXX-uc.a.run.app`

## Architecture

```
User → Cloud Run (FastAPI + React)
              ↓
        AI Agent Loop (Claude + web search)
              ↓              ↓              ↓
     Cloud Storage      BigQuery      Secret Manager
   (raw artifacts)   (run history)    (API keys)
```

## Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| AI | Anthropic Claude (claude-sonnet-4), web_search tool |
| Frontend | React |
| Hosting | GCP Cloud Run (serverless containers) |
| Storage | GCP Cloud Storage (JSON artifacts) |
| Analytics | GCP BigQuery (run history + queries) |
| Secrets | GCP Secret Manager |
| CI/CD | GCP Cloud Build |

## Quick Start (Local)

```bash
# 1. Clone and install
git clone <your-repo>
cd research-agent
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Fill in GCP_PROJECT_ID, GCS_BUCKET_NAME, ANTHROPIC_API_KEY

# 3. Run locally
uvicorn app.main:app --reload --port 8080

# 4. Test it
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe"}'
```

## Deploy to GCP

```bash
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID us-central1
```

The script will:
1. Enable all required GCP APIs
2. Create a Cloud Storage bucket
3. Store your Anthropic API key in Secret Manager
4. Create a service account with least-privilege IAM roles
5. Set up the BigQuery dataset and table
6. Build your Docker image via Cloud Build
7. Deploy to Cloud Run and return the live URL

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/research` | Run research on a company |
| `GET` | `/history` | Query recent runs from BigQuery |
| `GET` | `/health` | Health check |

### Example Request

```bash
curl -X POST https://YOUR_URL/research \
  -H "Content-Type: application/json" \
  -d '{"company": "OpenAI"}'
```

### Example Response

```json
{
  "run_id": "a3f8c1d2",
  "company": "OpenAI",
  "brief": {
    "summary": "OpenAI is an AI research company...",
    "industry": "Artificial Intelligence",
    "business_model": "API access, ChatGPT subscriptions, enterprise licensing",
    "key_products": ["ChatGPT", "GPT-4", "DALL-E", "Whisper", "Sora"],
    "competitors": ["Anthropic", "Google DeepMind", "Meta AI"],
    "sentiment": "positive",
    "interview_tip": "Ask about their approach to safety vs. capability tradeoffs"
  },
  "artifact_url": "gs://your-bucket/research/a3f8c1d2_OpenAI.json",
  "timestamp": "2025-06-01T12:00:00Z"
}
```

## BigQuery Analytics

Once you have data, run queries in the GCP console:

```sql
-- Most researched companies
SELECT company, COUNT(*) as searches
FROM `your-project.research_agent.runs`
GROUP BY company ORDER BY searches DESC;

-- Sentiment breakdown
SELECT sentiment, COUNT(*) as count
FROM `your-project.research_agent.runs`
GROUP BY sentiment;
```

## Cost Estimate

With ~100 research runs/month:
- **Cloud Run**: ~$0 (free tier covers it)
- **Cloud Storage**: ~$0.01
- **BigQuery**: ~$0 (free tier)
- **Anthropic API**: ~$2–5 depending on search depth
- **Total: ~$2–5/month**
