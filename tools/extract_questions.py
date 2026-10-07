"""
One-shot extraction script: turns the ML4T Exam Question Pool PDF into
app/data/ml4t_bank.json (ML Part 1 + QF Part 1 only, per project scope).

Usage:
    python tools/extract_questions.py "/path/to/ML4T Exam Question Pool.pdf"

Requires PyMuPDF: uv pip install pymupdf

Why this exists as a standalone script (not part of the running app):
the question bank never changes at runtime, so there's no reason to pay
the PDF-parsing cost on every server start. Run this once, commit the
resulting JSON, done (YAGNI).
"""
import re
import sys
import json
from pathlib import Path

ML1_TITLE = "Machine Learning – Part 1"
QF1_TITLE = "Quantitative Finance – Part 1"
ML2_TITLE = "Machine Learning – Part 2"

ID_RE = re.compile(r'^\[(ML|QF)-D(\d+)G(\d+)Q(\d+)\]$')
DOMAIN_RE = re.compile(r'^Domain (\d+):\s*(.+)$')
GROUP_RE = re.compile(r'^G(\d+):\s*(.+)$')
STMT_RE = re.compile(r'^([A-E])\.\s+(.*)$')
ANSWER_HEADER_RE = re.compile(r'^Answer Key\s*(\(.*\))?\s*:?\s*$', re.IGNORECASE)
ANSWER_STMT_RE = re.compile(r'^([A-E])\.\s*(True|False)\s*[–\-:]*\s*(.*)$')

# Known PDF font/ligature extraction artifacts -> their real meaning.
# Confirmed by inspecting repeated, unambiguous contexts (e.g. "TradeoƯs" -> "Tradeoffs").
SUBSCRIPT_MAP = {
    '\u0b34': '\u2080', '\u0b35': '\u2081', '\u0b36': '\u2082',
    '\u0b37': '\u2083', '\u0b38': '\u2084', '\u0b39': '\u2085',
}


def extract_pdf_text(pdf_path):
    import pymupdf
    doc = pymupdf.open(pdf_path)
    lines = []
    for page in doc:
        lines.append(f"===PAGE {page.number + 1}===")
        lines.extend(page.get_text().split('\n'))
    return lines


def clean_lines(raw_lines):
    out = []
    for raw in raw_lines:
        s = raw.strip()
        if not s or s.startswith('===PAGE') or s.startswith('Rev:'):
            continue
        if re.fullmatch(r'\d+', s):
            continue
        out.append(s)
    return out


def slice_between(lines, start_marker, end_marker):
    """Return lines strictly between the 2nd occurrence of start_marker
    (1st is the table of contents) and the 2nd occurrence of end_marker."""
    def second_occurrence(marker):
        hits = [i for i, l in enumerate(lines) if marker in l]
        return hits[1]
    start = second_occurrence(start_marker)
    end = second_occurrence(end_marker)
    return lines[start:end]


def fix_text(t):
    if not t:
        return t
    t = t.replace('\u01af', 'ff')      # ligature glyph -> "ff"
    for k, v in SUBSCRIPT_MAP.items():
        t = t.replace(k, v)
    t = t.replace('\u0ddc', '\u0302')  # combining "hat" accent (e.g. y-hat)
    t = t.replace('\u0dcd', '\u03a3')  # summation sigma
    t = t.replace('\u0b40', '=')       # "=" inside a subscript (e.g. i=1)
    t = t.replace('\uf0b7', '')        # stray bullet glyph
    return re.sub(r'\s+', ' ', t).strip()


def parse_section(lines):
    """Parse one Part's worth of cleaned lines into a list of domain dicts."""
    n = len(lines)

    # "Live" group headers: a "G#: Title" line immediately followed by a
    # question id. (The same text also appears earlier as a plain summary
    # header followed by bullet points - we must not confuse the two.)
    live_group_at = {}
    for i, l in enumerate(lines):
        m = GROUP_RE.match(l)
        if not m:
            continue
        for j in range(i + 1, min(i + 3, n)):
            if ID_RE.match(lines[j]):
                live_group_at[i] = (m.group(1), m.group(2))
                break

    domain_starts = []
    for i, l in enumerate(lines):
        m = DOMAIN_RE.match(l)
        if not m:
            continue
        for j in range(i + 1, min(i + 3, n)):
            if lines[j] == 'Domain Summary':
                domain_starts.append((i, m.group(1), m.group(2)))
                break

    domains = []
    for di, (start_idx, dnum, dtitle) in enumerate(domain_starts):
        end_idx = domain_starts[di + 1][0] if di + 1 < len(domain_starts) else n
        dom_lines = lines[start_idx:end_idx]
        dom_live_groups = sorted(
            (idx - start_idx, gnum, gtitle)
            for idx, (gnum, gtitle) in live_group_at.items()
            if start_idx <= idx < end_idx
        )

        def group_for(local_idx, groups=dom_live_groups):
            best = None
            for hidx, gnum, gtitle in groups:
                if hidx < local_idx:
                    best = (gnum, gtitle)
                else:
                    break
            return best

        id_positions = [i for i, l in enumerate(dom_lines) if ID_RE.match(l)]
        questions = []
        for qi, idpos in enumerate(id_positions):
            idm = ID_RE.match(dom_lines[idpos])
            qend = id_positions[qi + 1] if qi + 1 < len(id_positions) else len(dom_lines)
            block = dom_lines[idpos + 1:qend]
            gnum, gtitle = group_for(idpos) or (idm.group(3), "Unknown Group")

            scenario_parts, statements, answers = [], {}, {}
            mode, cur_letter, answer_note = 'scenario', None, None
            for l in block:
                am = ANSWER_HEADER_RE.match(l)
                if am:
                    mode, answer_note, cur_letter = 'answerkey', am.group(1), None
                    continue
                if mode == 'scenario':
                    sm = STMT_RE.match(l)
                    if sm:
                        mode, cur_letter = 'statements', sm.group(1)
                        statements[cur_letter] = sm.group(2)
                    else:
                        scenario_parts.append(l)
                elif mode == 'statements':
                    sm = STMT_RE.match(l)
                    if sm:
                        cur_letter = sm.group(1)
                        statements[cur_letter] = sm.group(2)
                    elif cur_letter:
                        statements[cur_letter] += ' ' + l
                elif mode == 'answerkey':
                    sm = ANSWER_STMT_RE.match(l)
                    if sm:
                        cur_letter = sm.group(1)
                        answers[cur_letter] = [sm.group(2) == 'True', sm.group(3)]
                    elif cur_letter:
                        answers[cur_letter][1] += ' ' + l

            questions.append({
                'id': f"{idm.group(1)}-D{idm.group(2)}G{idm.group(3)}Q{idm.group(4)}",
                'domain_num': int(dnum),
                'domain_title': fix_text(dtitle),
                'group_num': int(gnum),
                'group_title': fix_text(gtitle),
                'scenario': fix_text(' '.join(scenario_parts)),
                'answer_note': fix_text(answer_note) if answer_note else None,
                'statements': [
                    {
                        'letter': L,
                        'text': fix_text(statements.get(L, '')),
                        'answer': answers.get(L, [None, ''])[0],
                        'explanation': fix_text(answers.get(L, [None, ''])[1]),
                    }
                    for L in ['A', 'B', 'C', 'D', 'E'] if L in statements
                ],
            })
        domains.append({'domain_num': int(dnum), 'domain_title': fix_text(dtitle), 'questions': questions})
    return domains


def build_bank(domains, subject):
    out_domains, all_questions = [], {}
    for d in domains:
        groups, dom_qids = {}, []
        for q in d['questions']:
            qid = q['id']
            dom_qids.append(qid)
            groups.setdefault(q['group_num'], {'num': q['group_num'], 'title': q['group_title'], 'question_ids': []})
            groups[q['group_num']]['question_ids'].append(qid)
            all_questions[qid] = {**q, 'subject': subject}
        out_domains.append({
            'num': d['domain_num'],
            'title': d['domain_title'],
            'question_ids': dom_qids,
            'groups': [groups[k] for k in sorted(groups)],
        })
    out_domains.sort(key=lambda x: x['num'])
    return out_domains, all_questions


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_questions.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    raw_lines = extract_pdf_text(pdf_path)
    ml1_raw = clean_lines(slice_between(raw_lines, ML1_TITLE, QF1_TITLE))
    qf1_raw = clean_lines(slice_between(raw_lines, QF1_TITLE, ML2_TITLE))

    ml_domains, ml_questions = build_bank(parse_section(ml1_raw), 'ML')
    qf_domains, qf_questions = build_bank(parse_section(qf1_raw), 'QF')

    bank = {
        'subjects': {
            'ML': {'label': ML1_TITLE, 'domains': ml_domains},
            'QF': {'label': QF1_TITLE, 'domains': qf_domains},
        },
        'questions': {**ml_questions, **qf_questions},
    }

    out_path = Path(__file__).parent.parent / 'app' / 'data' / 'ml4t_bank.json'
    out_path.write_text(json.dumps(bank, indent=1), encoding='utf-8')
    print(f"Wrote {len(bank['questions'])} questions to {out_path}")


if __name__ == '__main__':
    main()
