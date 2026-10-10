"""Merge talk index + per-talk metadata into speeches.json / speeches.csv."""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).parent
idx = list(csv.DictReader(open(ROOT / "talk_index.tsv", encoding="utf-8"), delimiter="\t"))
meta = {}
for line in open(ROOT / "meta.jsonl", encoding="utf-8"):
    line = line.strip()
    if line:
        m = json.loads(line)
        meta[m["url"]] = m

SPEAKERS = {
    "Dallin H. Oaks": {
        "slug": "dallin-h-oaks",
        "born": "1932-08-12",
        "died": None,
        "current_title": "President of The Church of Jesus Christ of Latter-day Saints (since October 2025)",
        "roles": [
            "President of Brigham Young University (1971–1980)",
            "Justice, Utah Supreme Court (1980–1984)",
            "Quorum of the Twelve Apostles (1984–2018)",
            "First Counselor in the First Presidency (2018–2025)",
            "President of the Church (2025– )",
        ],
        "summary": "Lawyer, law professor, and former BYU president; former Utah Supreme Court justice; became the Church's eighteenth president in October 2025.",
        "byu_page": "https://speeches.byu.edu/speakers/dallin-h-oaks/",
    },
    "Russell M. Nelson": {
        "slug": "russell-m-nelson",
        "born": "1924-09-09",
        "died": "2025-09-27",
        "current_title": "Seventeenth President of The Church of Jesus Christ of Latter-day Saints (2018–2025)",
        "roles": [
            "Sunday School General President (1971–1979)",
            "Quorum of the Twelve Apostles (1984–2018)",
            "President of the Quorum of the Twelve (2015–2018)",
            "President of the Church (2018–2025)",
        ],
        "summary": "Pioneering heart surgeon who helped make open-heart surgery possible; apostle for over thirty years before leading the Church. Died September 27, 2025, at 101.",
        "byu_page": "https://speeches.byu.edu/speakers/russell-m-nelson/",
    },
    "M. Russell Ballard": {
        "slug": "m-russell-ballard",
        "born": "1928-10-08",
        "died": "2023-11-12",
        "current_title": "Acting President of the Quorum of the Twelve Apostles (2018–2023)",
        "roles": [
            "Canada Toronto Mission President (1974–1976)",
            "Seventy (1976–1985)",
            "Quorum of the Twelve Apostles (1985–2023)",
            "Acting President of the Quorum of the Twelve (2018–2023)",
        ],
        "summary": "Businessman in automotive, real estate, and investments before full-time Church service; called to the Seventy in 1976 and the Twelve in 1985. Died November 12, 2023.",
        "byu_page": "https://speeches.byu.edu/speakers/m-russell-ballard/",
    },
}

HISTORY = {  # (start date, role) — role held from that date on
    "Dallin H. Oaks": [("1971-08-01", "BYU President"), ("1980-08-01", "Utah Supreme Court"),
                       ("1984-05-03", "Quorum of the Twelve"), ("2018-01-14", "First Presidency"),
                       ("2025-10-14", "President of the Church")],
    "Russell M. Nelson": [("1971-01-01", "Sunday School General President"),
                          ("1984-04-07", "Quorum of the Twelve"), ("2018-01-14", "President of the Church")],
    "M. Russell Ballard": [("1976-10-01", "Seventy"), ("1985-10-10", "Quorum of the Twelve")],
}

def role_group(speaker, position, date):
    """Normalized role at the time of the talk, from each speaker's service history.
    Returns (group, differs_from_listed): the flag marks talks where the page lists no
    position or a position that doesn't match the date."""
    group = "Unknown"
    for start, role in HISTORY[speaker]:
        if date >= start:
            group = role
    listed = _listed_group(position)
    return group, (listed != group)

def _listed_group(position):
    p = (position or "").lower()
    if "president of the church" in p or "president of the church of jesus christ" in p:
        return "President of the Church"
    if "first presidency" in p:
        return "First Presidency"
    if "twelve" in p:
        return "Quorum of the Twelve"
    if "seventy" in p:
        return "Seventy"
    if "brigham young university" in p:
        return "BYU President"
    if "supreme court" in p:
        return "Utah Supreme Court"
    if "sunday school" in p:
        return "Sunday School General President"
    return None

def tidy_position(pos):
    if not pos:
        return ""
    pos = pos.strip()
    return pos[0].upper() + pos[1:]

def runtime_min(rt):
    if not rt:
        return None
    parts = [int(x) for x in rt.split(":")]
    secs = parts[-1] + parts[-2] * 60 + (parts[-3] * 3600 if len(parts) == 3 else 0)
    return round(secs / 60, 1)

records = []
for row in idx:
    m = meta[row["url"]]
    assert m["date"] == row["date"], (row["url"], m["date"], row["date"])
    sp = SPEAKERS[row["speaker"]]
    talk_slug = row["url"].rstrip("/").split("/")[-1]
    group, inferred = role_group(row["speaker"], m["position"], row["date"])
    records.append({
        "id": f'{sp["slug"]}/{talk_slug}',
        "speaker": row["speaker"],
        "speaker_slug": sp["slug"],
        "title": row["title"],
        "date": row["date"],
        "year": int(row["date"][:4]),
        "event": m["event"],
        "position_listed": tidy_position(m["position"]),
        "role_group": group,
        "role_note": inferred,
        "topics": m["topics"],
        "has_audio": m["audio"],
        "has_video": m["video"],
        "has_pdf": m["pdf"],
        "runtime": m["runtime"],
        "runtime_min": runtime_min(m["runtime"]),
        "read_min": m["read_min"],
        "byu_url": row["url"],
    })

records.sort(key=lambda r: r["date"], reverse=True)
out = {
    "generated": "2026-10-10",
    "source": "https://speeches.byu.edu",
    "speakers": [{"name": k, **v, "talk_count": sum(r["speaker"] == k for r in records)} for k, v in SPEAKERS.items()],
    "talks": records,
}
(ROOT / "data").mkdir(exist_ok=True)
json.dump(out, open(ROOT / "data/speeches.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

cols = ["speaker", "title", "date", "year", "event", "position_listed", "role_group", "role_note",
        "topics", "has_audio", "has_video", "has_pdf", "runtime", "runtime_min", "read_min", "byu_url"]
with open(ROOT / "data/speeches.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for r in records:
        w.writerow(["; ".join(r[c]) if c == "topics" else r[c] for c in cols])

from collections import Counter
print(Counter(r["speaker"] for r in records))
print(Counter(r["event"] for r in records))
print(Counter(r["role_group"] for r in records))
print("role_note:", [r["id"] for r in records if r["role_note"]])
print("topics:", len({t for r in records for t in r["topics"]}))
