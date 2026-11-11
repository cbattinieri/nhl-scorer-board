"""Turn docs/status.json into the daily email's subject and HTML body.

Run by .github/workflows/daily_email.yml. Writes email.html and sets `subject`
on $GITHUB_OUTPUT.

The freshness check is done HERE, at send time, not read from the file. The
age fields in status.json were computed when the laptop built the page, which
may have been yesterday; trusting them would let a stale board announce itself
as fresh. What the file can be trusted for is the slate DATE it was built for,
so that is what gets compared against today.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import zoneinfo

ET = zoneinfo.ZoneInfo("America/New_York")
URL = "https://cbattinieri.github.io/nhl-scorer-board/"
STATUS = pathlib.Path("docs/status.json")

CSS = """
body{margin:0;background:#F5F7F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0C1821}
.w{max-width:640px;margin:0 auto;padding:22px 18px}
h1{font-size:19px;margin:0 0 3px}
.sub{color:#5B6B79;font-size:13px;margin:0 0 16px}
.stamps{background:#FFF;border:1px solid #D9E1E8;border-radius:9px;padding:12px 14px;margin-bottom:14px;font-size:13px}
.stamps div{padding:2px 0}
.stamps b{display:inline-block;min-width:124px;color:#5B6B79;font-weight:600}
.warn{background:#F8E7E4;border-left:3px solid #A8483D;color:#8A3024;padding:11px 13px;border-radius:0 8px 8px 0;margin-bottom:14px;font-size:13px}
.note{background:#F7EEDA;border-left:3px solid #8A6410;color:#6B4E0C;padding:11px 13px;border-radius:0 8px 8px 0;margin-bottom:16px;font-size:12.5px}
table{border-collapse:collapse;width:100%;background:#FFF;border:1px solid #D9E1E8;border-radius:9px;font-size:13px}
th{text-align:right;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:#5B6B79;padding:9px 10px;background:#EDF1F5;border-bottom:1px solid #D9E1E8}
th:first-child{text-align:left}
td{padding:9px 10px;text-align:right;border-bottom:1px solid #EDF1F5}
td:first-child{text-align:left;font-weight:600}
tr:last-child td{border-bottom:none}
.btn{display:inline-block;background:#14657F;color:#FFF!important;text-decoration:none;padding:11px 20px;border-radius:8px;font-weight:600;font-size:14px;margin:18px 0 6px}
.ft{color:#5B6B79;font-size:11.5px;margin-top:14px;line-height:1.5}
"""


def main() -> None:
    now = dt.datetime.now(ET)
    today = now.date().isoformat()

    if not STATUS.exists():
        subject = "Scorer Board — nothing published yet"
        body = block("No board has been published yet.",
                     "The build machine has not pushed a slate to this repo.")
        finish(subject, body)
        return

    s = json.loads(STATUS.read_text(encoding="utf-8"))
    slate = s.get("slate_date") or "unknown"
    stale = slate != today

    if stale:
        subject = f"Scorer Board — STALE, still showing {slate}"
    else:
        subject = (f"Scorer Board — {fmt_date(slate)}, "
                   f"{s.get('games', 0)} games, {s.get('priced', 0)} priced")

    parts = []
    if stale:
        parts.append(
            f'<div class="warn"><b>The board did not update today.</b> '
            f'It still shows the {html.escape(slate)} slate — the build machine '
            f'was asleep or its run failed. Everything below is out of date.</div>')

    parts.append(
        '<div class="stamps">'
        f'<div><b>Model refreshed</b> {html.escape(str(s.get("model_refreshed") or "never"))}</div>'
        f'<div><b>Odds refreshed</b> {html.escape(str(s.get("odds_refreshed") or "never"))}</div>'
        f'<div><b>Page built</b> {html.escape(str(s.get("built") or "never"))}</div>'
        f'<div><b>Slate</b> {html.escape(slate)} &middot; {s.get("games", 0)} games &middot; '
        f'{s.get("priced", 0)} of {s.get("skaters", 0)} skaters priced</div>'
        '</div>')

    top = s.get("top") or []
    if top and not stale:
        parts.append(
            '<div class="note"><b>Longshots are already excluded.</b> At +600 and out, '
            'expected value is dominated by model error on a tiny probability rather than '
            'by real disagreement with the book. The model also runs hot overall.</div>')
        rows = "".join(
            f'<tr><td>{html.escape(t["name"])} <span style="color:#5B6B79;font-weight:400">'
            f'{html.escape(t.get("pos") or "")}</span><br>'
            f'<span style="color:#5B6B79;font-weight:400;font-size:11.5px">'
            f'{html.escape(t.get("matchup") or "")}</span></td>'
            f'<td>{t["model"] * 100:.1f}%</td>'
            f'<td>{t["market"] * 100:.1f}%</td>'
            f'<td>{"+" if t["best"] > 0 else ""}{t["best"]}</td>'
            f'<td style="color:#2E7A5A;font-weight:600">+{t["ev"] * 100:.0f}%</td></tr>'
            for t in top)
        parts.append(
            '<table><tr><th>Skater</th><th>Model</th><th>Market</th>'
            f'<th>Best</th><th>EV</th></tr>{rows}</table>')

    parts.append(f'<a class="btn" href="{URL}">Open the full board</a>')
    parts.append(
        '<div class="ft">Research output, not betting advice. '
        'Expected value is computed at the single best price across books, which '
        'naturally picks whichever book is furthest off.<br>'
        f'Sent {now.strftime("%b %d, %I:%M %p").replace(" 0", " ")} ET by the '
        'daily_email workflow.</div>')

    finish(subject, "".join(parts))


def block(title: str, detail: str) -> str:
    return (f'<div class="warn"><b>{html.escape(title)}</b><br>{html.escape(detail)}</div>'
            f'<a class="btn" href="{URL}">Open the board</a>')


def fmt_date(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
        return d.strftime("%b %d").replace(" 0", " ")
    except ValueError:
        return iso


def finish(subject: str, body: str) -> None:
    page = (f'<html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div class="w"><h1>Scorer Board</h1>'
            f'<p class="sub">NHL anytime goal scorer — model against the market</p>'
            f'{body}</div></body></html>')
    pathlib.Path("email.html").write_text(page, encoding="utf-8")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"subject={subject}\n")
    print(f"subject: {subject}")
    print(f"body: {len(page)} bytes -> email.html")


if __name__ == "__main__":
    main()
