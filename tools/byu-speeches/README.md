# BYU Speeches section for claytonchevrier.org

Source data and build scripts for the live `/speeches/` section at the repo root
and the "BYU Speeches" card on the home page (`index.html`).

Rebuild:

```
python3 build_data.py && python3 build_site.py
```

This writes `site/speeches/` and `site/home-section.html` here in `tools/byu-speeches/`.
Then copy the regenerated files into the live site:

- `site/speeches/*` -> repo root `speeches/` (overwrite)
- `site/home-section.html` -> re-paste the link/copy into the BYU Speeches card in `index.html` if it changed (e.g. talk count)

To refresh the underlying data, update `talk_index.tsv` (speaker, title, date, url)
and `meta.jsonl` (one JSON object per talk URL: position, event, topics, audio/video/pdf, runtime, read_min)
before running `build_data.py`.
