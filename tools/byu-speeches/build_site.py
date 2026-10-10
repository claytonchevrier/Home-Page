"""Generate the BYU Speeches section of claytonchevrier.org.

Output (site/ is the deployable folder; its contents go at the site root):
  site/speeches/index.html               speakers page (cards with full speaker details)
  site/speeches/<speaker-slug>/index.html one talk list per speaker
  site/speeches/speeches.json, .csv      the data
  site/home-section.html                 snippet for the claytonchevrier.org home page
Also builds preview/ (same pages, links that work inside a Claude artifact).
"""
import csv, html, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.load(open(ROOT / "data/speeches.json", encoding="utf-8"))
COLOR = {"dallin-h-oaks": "var(--oaks)", "russell-m-nelson": "var(--nelson)", "m-russell-ballard": "var(--ballard)"}
e = lambda s: html.escape(str(s or ""), quote=True)

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one column, max 1180px; speakers page = card grid, speaker page = the same speaker card beside a sortable talk register */
:root {
  --bg: #f6f7f9; --surface: #ffffff; --ink: #18202e; --muted: #5b6577; --line: #dde1e8;
  --accent: #1f4f8f; --chip: #eef0f4;
  --oaks: #1f4f8f; --nelson: #8a4b16; --ballard: #2f6b4f;
  --font-display: "Newsreader", Georgia, "Times New Roman", serif;
  --font-body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #11151c; --surface: #181e28; --ink: #e6e9ef; --muted: #98a2b3; --line: #2a3240;
  --accent: #7fb0ec; --chip: #222a37; --oaks: #7fb0ec; --nelson: #e3a46c; --ballard: #7fc9a3; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #11151c; --surface: #181e28; --ink: #e6e9ef; --muted: #98a2b3; --line: #2a3240;
  --accent: #7fb0ec; --chip: #222a37; --oaks: #7fb0ec; --nelson: #e3a46c; --ballard: #7fc9a3; color-scheme: dark }
* { box-sizing: border-box }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 var(--font-body); }
.wrap { max-width: 1180px; margin: 0 auto; padding-inline: 20px; padding-block: 24px 48px; }
a { color: var(--accent) }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.crumbs { font-size: .85rem; color: var(--muted); margin-bottom: 14px; display: flex; gap: 6px; flex-wrap: wrap; }
.crumbs a { text-decoration: none } .crumbs a:hover { text-decoration: underline }
h1 { font: 600 clamp(1.7rem, 3.4vw, 2.4rem)/1.15 var(--font-display); margin: 0 0 6px; text-wrap: balance; }
.lede { color: var(--muted); margin: 0 0 24px; max-width: 68ch; }
.lbl { font: 600 .72rem var(--font-body); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
/* speaker card (used on both pages) */
.card { background: var(--surface); border: 1px solid var(--line); border-top: 4px solid var(--c); border-radius: 8px; padding: 18px 20px; display: grid; gap: 10px; align-content: start; color: var(--ink); text-decoration: none; }
.card h2 { font: 600 1.45rem/1.15 var(--font-display); margin: 0; text-wrap: balance; }
.card .life { font: .82rem var(--font-mono); color: var(--muted); }
.card .ttl { font-weight: 500; }
.card p { margin: 0; color: var(--muted); font-size: .92rem; max-width: 70ch; }
.card ul { margin: 0; padding-left: 18px; font-size: .88rem; display: grid; gap: 2px; }
.card .stats { display: flex; flex-wrap: wrap; gap: 6px 18px; font: .84rem var(--font-mono); color: var(--muted); font-variant-numeric: tabular-nums; }
.card .stats b { color: var(--ink); font-weight: 500; }
.card .go { font-weight: 600; color: var(--accent); }
a.card:hover { border-color: var(--c); box-shadow: 0 0 0 1px var(--c) inset; }
a.card:hover .go { text-decoration: underline; }
@media (prefers-reduced-motion: no-preference) { a.card { transition: border-color .15s, box-shadow .15s } }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.foot { margin-top: 22px; font-size: .8rem; color: var(--muted); max-width: 80ch; }
</style>"""

LIST_CSS = """<style>
.main { display: grid; grid-template-columns: minmax(300px, 370px) minmax(0, 1fr); gap: 24px; align-items: start; }
.main > .card { position: sticky; top: calc(env(safe-area-inset-top, 0px) + 12px); }
@media (max-width: 900px) { .main { grid-template-columns: 1fr } .main > .card { position: static } }
.main .go { text-decoration: none } .main .go:hover { text-decoration: underline }
select { font: inherit; font-size: .9rem; padding: 7px 9px; border: 1px solid var(--line); border-radius: 6px; background: var(--surface); color: var(--ink); }
.bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 10px; }
.count { font: 500 .9rem var(--font-mono); color: var(--muted); }
.sortm { display: none; gap: 6px; align-items: center; } .sortm select { width: auto }
.tbl { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th { text-align: left; font: 600 .72rem var(--font-body); letter-spacing: .07em; text-transform: uppercase; color: var(--muted); padding: 10px 12px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th button { all: unset; cursor: pointer; } th button:focus-visible { outline: 2px solid var(--accent); }
th button[aria-sort]::after { content: " " attr(data-dir); color: var(--accent); }
td { padding: 11px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
tbody tr:last-child td { border-bottom: 0 }
.d { font: .82rem var(--font-mono); white-space: nowrap; font-variant-numeric: tabular-nums; }
.num { font: .82rem var(--font-mono); text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.t a { font: 600 1.02rem/1.3 var(--font-display); color: var(--ink); text-decoration: none; }
.t a:hover { color: var(--accent); text-decoration: underline; }
.t a .ext { font: .75rem var(--font-body); color: var(--muted); margin-left: 4px; }
.pos { font-size: .8rem; color: var(--muted); }
.tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; }
.tag { font-size: .74rem; padding: 1px 7px; border-radius: 10px; background: var(--chip); color: var(--muted); }
.note { font-size: .74rem; color: var(--muted); font-style: italic; }
@media (max-width: 720px) {
  /* Phone: each talk becomes a compact block — date · length on top, title, calling, topics */
  thead { display: none } .sortm { display: flex }
  table, tbody { display: block; width: 100% }
  tbody tr { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 10px; padding: 12px 14px; border-bottom: 1px solid var(--line); }
  tbody tr:last-child { border-bottom: 0 }
  td { display: block; padding: 0; border: 0; }
  .d { order: 1; color: var(--muted); }
  .num { order: 2; text-align: left; color: var(--muted); }
  .num:not(:empty)::before { content: "· "; }
  .t { order: 3; width: 100%; }
  .t .pos { display: none; }
  .cl { order: 4; width: 100%; font-size: .82rem; color: var(--muted); }
  .cl .note { display: inline; margin-left: 6px; }
  .t .tags { order: 5; }
  .t a { font-size: 1.08rem; display: inline-block; padding-block: 2px; }
  .tag { font-size: .72rem; }
  .card { padding: 16px; }
}
</style>"""

FOOT = """<p class="foot">Talks and speaker details from <a href="https://speeches.byu.edu" target="_blank" rel="noopener">BYU Speeches</a>, collected {gen}. Talk links open the talk on speeches.byu.edu in a new tab.</p>"""


def speaker_card(s, talks, link=None, back=None):
    years = [t["year"] for t in talks]
    life = f'{s["born"][:4]}–{s["died"][:4] if s["died"] else ""}'
    roles = "".join(f"<li>{e(r)}</li>" for r in s["roles"])
    inner = f"""
    <h2>{e(s["name"])}</h2>
    <div class="life">{life}{" · died " + e(fmt_long(s["died"])) if s["died"] else ""}</div>
    <div class="ttl">{e(s["current_title"])}</div>
    <p>{e(s["summary"])}</p>
    <div><div class="lbl">Callings</div><ul>{roles}</ul></div>
    <div class="stats"><span><b>{len(talks)}</b> talks</span><span><b>{min(years)}–{max(years)}</b></span></div>"""
    if link:
        return f'<a class="card" href="{e(link)}" style="--c:{COLOR[s["slug"]]}">{inner}\n    <span class="go">View {len(talks)} talks →</span></a>'
    return f'<section class="card" style="--c:{COLOR[s["slug"]]}" aria-label="About {e(s["name"])}">{inner}\n    <a class="go" href="{e(back)}">← All speakers</a></section>'


def fmt_long(iso):
    from datetime import date
    d = date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def doc(title, body, extra_css="", bare=False):
    head = f"<title>{e(title)}</title>\n{HEAD}\n{extra_css}"
    if bare:  # artifact main page: the publisher adds the document skeleton
        return head.replace('<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n', "") + "\n" + body + "\n"
    return f'<!doctype html>\n<html lang="en">\n<head>\n{head}\n</head>\n<body>\n{body}\n</body>\n</html>\n'


def speakers_page(home, sp_href, bare=False):
    cards = "\n".join(speaker_card(s, [t for t in DATA["talks"] if t["speaker_slug"] == s["slug"]], sp_href(s["slug"])) for s in DATA["speakers"])
    body = f"""<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">claytonchevrier.org</a><span>/</span><span>BYU Speeches</span></nav>
  <h1>BYU Speeches</h1>
  <p class="lede">Talks given at Brigham Young University by three Church leaders, from the BYU Speeches archive. Choose a speaker to see all of their talks.</p>
  <div class="grid">
{cards}
  </div>
  {FOOT.format(gen=e(DATA["generated"]))}
</div>"""
    return doc("BYU Speeches", body, bare=bare)


def speaker_page(s, home, up):
    talks = [t for t in DATA["talks"] if t["speaker_slug"] == s["slug"]]
    slim = [{k: t[k] for k in ("title", "date", "year", "position_listed", "role_group", "role_note", "topics", "runtime", "runtime_min", "byu_url")} for t in talks]
    js_data = json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")
    body = f"""<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">claytonchevrier.org</a><span>/</span><a href="{up}">BYU Speeches</a><span>/</span><span>{e(s["name"])}</span></nav>
  <div class="main">
    {speaker_card(s, talks, back=up)}
    <section style="min-width:0">
      <div class="bar">
        <span class="count" id="count"></span>
        <div class="sortm"><label for="sortSel" class="lbl">Sort</label>
          <select id="sortSel"><option value="date:desc">Newest first</option><option value="date:asc">Oldest first</option>
            <option value="title:asc">Title A–Z</option><option value="runtime_min:desc">Longest</option><option value="runtime_min:asc">Shortest</option></select></div>
      </div>
      <div class="tbl"><table>
        <thead><tr>
          <th><button type="button" data-k="date">Date</button></th>
          <th><button type="button" data-k="title">Talk</button></th>
          <th><button type="button" data-k="role_group">Calling</button></th>
          <th style="text-align:right"><button type="button" data-k="runtime_min">Length</button></th>
        </tr></thead>
        <tbody id="rows"></tbody>
      </table>
      </div>
    </section>
  </div>
  {FOOT.format(gen=e(DATA["generated"]))}
</div>
<script>
const talks = {js_data};
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
const fmtDate = d => new Date(d + "T12:00:00").toLocaleDateString("en-US", {{year: "numeric", month: "short", day: "numeric"}});
let sortKey = "date", sortDir = -1;   // default: newest first
function cmp(a, b) {{
  let x = a[sortKey], y = b[sortKey];
  if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
  if (typeof x === "string") {{ if (sortKey === "title") {{ x = x.replace(/^["“]/, ""); y = y.replace(/^["“]/, ""); }} return x.localeCompare(y) * sortDir; }}
  return (x - y) * sortDir;
}}
function render() {{
  const list = [...talks].sort((a, b) => cmp(a, b) || b.date.localeCompare(a.date));
  $("count").textContent = `${{talks.length}} talks`;
  $("rows").innerHTML = list.map(t => `<tr>
    <td class="d">${{fmtDate(t.date)}}</td>
    <td class="t" style="min-width:0"><a href="${{esc(t.byu_url)}}" target="_blank" rel="noopener">${{esc(t.title)}}<span class="ext" aria-label="(opens BYU Speeches in a new tab)">↗</span></a>
      ${{t.position_listed ? `<div class="pos">${{esc(t.position_listed)}}</div>` : ""}}
      <div class="tags">${{t.topics.map(x => `<span class="tag">${{esc(x)}}</span>`).join("")}}</div></td>
    <td class="cl">${{esc(t.role_group)}}${{t.role_note ? `<div class="note">${{t.position_listed ? "page lists a different calling" : "not listed; by date"}}</div>` : ""}}</td>
    <td class="num">${{t.runtime ? esc(t.runtime) : ""}}</td></tr>`).join("");
  document.querySelectorAll("th button").forEach(b => {{
    if (b.dataset.k === sortKey) {{ b.setAttribute("aria-sort", sortDir > 0 ? "ascending" : "descending"); b.dataset.dir = sortDir > 0 ? "▲" : "▼"; }}
    else b.removeAttribute("aria-sort");
  }});
  const sv = `${{sortKey}}:${{sortDir > 0 ? "asc" : "desc"}}`;
  if ([...$("sortSel").options].some(o => o.value === sv)) $("sortSel").value = sv;
}}
document.querySelectorAll("th button").forEach(b => b.addEventListener("click", () => {{
  const k = b.dataset.k;
  if (k === sortKey) sortDir = -sortDir; else {{ sortKey = k; sortDir = (k === "date" || k === "runtime_min") ? -1 : 1; }}
  render();
}}));
$("sortSel").addEventListener("change", ev => {{ const [k, d] = ev.target.value.split(":"); sortKey = k; sortDir = d === "asc" ? 1 : -1; render(); }});
render();
</script>"""
    return doc(f'{s["name"]} — BYU Speeches', body, LIST_CSS)


HOME_SNIPPET = """<!-- BYU Speeches section for the claytonchevrier.org home page.
     Paste where you want the section; restyle freely to match the page. -->
<section class="byu-speeches" style="margin:2rem 0">
  <h2>BYU Speeches</h2>
  <p>Talks given at Brigham Young University by Dallin H. Oaks, Russell M. Nelson, and M. Russell Ballard, {n} in all, sorted by speaker.</p>
  <p><a href="/speeches/">Browse BYU Speeches →</a></p>
</section>
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build():
    for d in ("site", "preview"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    # Site: clean URLs (/speeches/, /speeches/<slug>/)
    write(ROOT / "site/speeches/index.html", speakers_page("/", lambda slug: f"/speeches/{slug}/"))
    for s in DATA["speakers"]:
        write(ROOT / f"site/speeches/{s['slug']}/index.html", speaker_page(s, "/", "/speeches/"))
    shutil.copy(ROOT / "data/speeches.json", ROOT / "site/speeches/speeches.json")
    shutil.copy(ROOT / "data/speeches.csv", ROOT / "site/speeches/speeches.csv")
    write(ROOT / "site/home-section.html", HOME_SNIPPET.format(n=len(DATA["talks"])))
    # Preview: relative file links that resolve inside a published artifact
    write(ROOT / "preview/index.html", speakers_page("https://claytonchevrier.org/", lambda slug: f"{slug}.html", bare=True))
    for s in DATA["speakers"]:
        write(ROOT / f"preview/{s['slug']}.html", speaker_page(s, "https://claytonchevrier.org/", "index.html"))


if __name__ == "__main__":
    build()
    print(sorted(str(p.relative_to(ROOT)) for p in (ROOT / "site").rglob("*") if p.is_file()))
