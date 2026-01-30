from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

APP = FastAPI(title="Berliner Bäder API")

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "pools.json"


@APP.get("/api/pools")
def get_pools() -> Any:
    """Return cached pools JSON. Do not trigger scraping here."""
    if not DATA_FILE.exists():
        raise HTTPException(status_code=503, detail="Data not available: pools.json missing")
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Data corrupted: invalid JSON")

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Data corrupted: expected list")

    return JSONResponse(content=data)


if __name__ == "__main__":
    # Simple dev runner
    import uvicorn

    uvicorn.run(APP, host="127.0.0.1", port=8000)
