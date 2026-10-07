# ML4T Exam Question Pool — Practice App

A self-study tool for the Georgia Tech ML4T exam question pool. Covers
**Machine Learning – Part 1** and **Quantitative Finance – Part 1** only
(Part 2 is out of scope). ML and QF question sets are kept fully separate —
no mixing.

- **518 questions** total (308 ML, 210 QF), each with 5 True/False statements,
  extracted verbatim from the official PDF question pool. No question text,
  answers, or explanations were altered — only PDF-ligature rendering
  artifacts (e.g. a garbled "ff" glyph) were corrected so the text displays
  properly.

## How it works

1. **Selection page (`/`)** — pick a subject tab (ML or QF), then choose
   specific topic **groups**, whole **domains** (all groups in that domain),
   or the **Final Part** (every domain in that subject). Toggle between
   original order or a randomized shuffle. Click "View Questions."
2. **Practice page (`/practice`)** — one question per page. Drag each of the
   5 statements into the **True** or **False** bucket (or just click the
   "Mark True"/"Mark False" buttons — no drag required). Click **Check
   Answer** to see per-statement correctness highlighting plus the original
   answer-key explanation. Reset to retry, or Next/Previous to move on.

## Running it

```bash
cd ~/ml4t-practice
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8420
```

Then open http://127.0.0.1:8420/

## Regenerating the question bank

The question data lives in `app/data/ml4t_bank.json`, generated once from
the source PDF via:

```bash
uv pip install pymupdf
python3 tools/extract_questions.py "/path/to/ML4T Exam Question Pool.pdf"
```

Only needs to be re-run if Walmart/GT publishes an updated question pool PDF.

## Known limitation

A handful of heavily mathematical statements (inline regression/portfolio
formulas with subscripts, summations, hat-accents) may show minor leftover
glyph artifacts — this is a PDF font-encoding quirk in the source document's
embedded math font, not a content change on our end. All question wording,
True/False answers, and explanations are otherwise complete and unmodified.
# ml4t-mid-sem
# ml4t-mid-sem
