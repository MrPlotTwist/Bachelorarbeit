# to start crawler:
# uvicorn app.main:app --reload

from fastapi import FastAPI, HTTPException
from playwright.sync_api import sync_playwright
import os
from fastapi.responses import FileResponse

from app.crawler_logic.models import CrawlRequest
from app.crawler_logic.crawler import crawl_urls
from app.db.database import get_run_results
from app.ai_integration.gpt_init import gpt_output
from pathlib import Path

app = FastAPI()


@app.post("/crawler")
def crawler_request(req: CrawlRequest):
    print("POST /crawler angekommen")

    with sync_playwright() as pw:
        run_id = crawl_urls(pw, req.url, req.max_pages)

    print(f"crawl_urls fertig, run_id={run_id}")

    db_results = get_run_results(run_id)

    report_result = gpt_output(db_output=db_results, run_id=run_id)

    # nach dem Speichern des Reports neu laden
    updated_db_results = get_run_results(run_id)

    print("Antwort wird ans Frontend zurückgegeben", flush=True)

    return {
        "run_id": run_id,
        "db_results": updated_db_results,
        "report_filename": report_result.get("report_filename"),
        "report_type": report_result.get("report_type"),
    }


#File download

REPORTS_PATH = Path(os.getenv("REPORTS_PATH", "security-reports"))
REPORTS_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/reports/{filename}")
def download_report(filename: str):
    safe_filename = Path(filename).name
    file_path = REPORTS_PATH / safe_filename

    print(f"[download_report] Angefragt: {safe_filename}", flush=True)
    print(f"[download_report] Voller Pfad: {file_path}", flush=True)
    print(f"[download_report] Existiert: {file_path.exists()}", flush=True)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report nicht gefunden")

    suffix = file_path.suffix.lower()
    media_type = "application/pdf" if suffix == ".pdf" else "text/plain"

    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type,
    )