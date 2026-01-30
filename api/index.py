from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Create FastAPI app
app = FastAPI(title="Berliner Bäder API")

# Path to cached data (works both locally and on Vercel)
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "pools.json"


@app.get("/api/pools")
def get_pools() -> Any:
    """Return cached pools JSON. Do not trigger scraping here."""
    if not DATA_FILE.exists():
        raise HTTPException(status_code=503, detail=f"Data not available: pools.json missing (looked at {DATA_FILE})")
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Data corrupted: invalid JSON — {e}")

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Data corrupted: expected list")

    return JSONResponse(content=data)


# Vercel expects 'app' as the ASGI application
# This is the entrypoint
