"""
ML4T Exam Question Pool - practice app.

Single-purpose FastAPI app that serves:
  GET /                selection page (pick domain/group/final-part per subject)
  GET /practice         one question per page, True/False bucket sorting

Question data is parsed once from the ML4T PDF into data/ml4t_bank.json
(see tools/extract_questions.py) and loaded read-only at startup - there's
no database because the content never changes at runtime (YAGNI).
"""
import json
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "ml4t_bank.json"

with open(DATA_PATH, encoding="utf-8") as f:
    BANK = json.load(f)

QUESTIONS = BANK["questions"]          # id -> question dict
SUBJECTS = BANK["subjects"]            # "ML" / "QF" -> {label, domains:[...]}

app = FastAPI(title="ML4T Practice")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
def selection_page(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"subjects": SUBJECTS},
    )


@app.get("/practice")
def practice_page(
    request: Request,
    qs: str = Query(..., description="comma separated question ids, in play order"),
    pos: int = Query(0, ge=0),
    subject: str = Query("ML"),
):
    ids = [q for q in qs.split(",") if q]
    total = len(ids)
    if total == 0:
        return RedirectResponse("/")
    pos = max(0, min(pos, total - 1))
    qid = ids[pos]
    question = QUESTIONS.get(qid)
    if question is None:
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request,
        "practice.html",
        {
            "question": question,
            "qs": qs,
            "pos": pos,
            "total": total,
            "subject": subject,
            "has_prev": pos > 0,
            "has_next": pos < total - 1,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8420)
