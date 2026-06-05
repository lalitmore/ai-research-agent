import os
import json
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import run_research_agent
from .gcp import upload_to_gcs, log_to_bigquery

app = FastAPI(title="AI Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    company: str


class ResearchResponse(BaseModel):
    run_id: str
    company: str
    brief: dict
    artifact_url: str
    timestamp: str


@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/research", response_model=ResearchResponse) # Pydantic validates the response matches the schema. If response doesn't match, return 500 error. 
async def research(req: ResearchRequest):   # the endpoint is async so it doesn't block while waiting for the AI agent. FastAPI can handle other requests while this one is running
    if not req.company.strip():
        raise HTTPException(status_code=400, detail="Company name required")

    run_id = str(uuid.uuid4())[:8] # Short unique ID for this run. Collision unlikely at this scale. 
    timestamp = datetime.now(timezone.utc).isoformat() # ISO format with timezone for easier querying and display.

    # 1. Run the AI agent
    brief = await run_research_agent(req.company)

    # 2. Save raw artifact to Cloud Storage
    artifact_path = f"research/{run_id}_{req.company.replace(' ', '_')}.json"
    artifact_url = upload_to_gcs(artifact_path, json.dumps(brief, indent=2))

    # 3. Log structured result to BigQuery
    log_to_bigquery({
        "run_id": run_id,
        "company": req.company,
        "timestamp": timestamp,
        "summary": brief.get("summary", ""),
        "sentiment": brief.get("sentiment", "neutral"),
        "topics_count": len(brief.get("key_topics", [])),
        "artifact_url": artifact_url,
    })

    return ResearchResponse(
        run_id=run_id,
        company=req.company,
        brief=brief,
        artifact_url=artifact_url,
        timestamp=timestamp,
    )


@app.get("/history")
def history(limit: int = 20):
    """Query recent research runs from BigQuery."""
    from .gcp import query_bigquery
    rows = query_bigquery(limit)
    return {"runs": rows}


# Serve React frontend (after `npm run build` output is in ./static)
# In production, it's better to serve the frontend separately (e.g. via Cloud Run or Firebase Hosting)
# and have it call the API, rather than serving static files from FastAPI. 
# But this is simpler for a demo and local testing.
# Cloud container serves frontend and API
if os.path.exists("static"):    
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
