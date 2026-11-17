# mistral

SEO Analyzer - a Flask web app that audits any page, extracts its main keywords, compares it against the pages ranking for a target keyword, and returns concrete, prioritized recommendations.

## Features

- **On-page audit** - title and meta description length, H1/subheadings, content length, image alt text, links, canonical, viewport, HTTPS, indexability, Open Graph tags, page size, load time.
- **Keyword extraction** - weighted TF scoring across title, meta description, H1-H3, and body text, with unigrams and bigrams, counts, and density.
- **Competition check** - for a target keyword, fetches the current top-ranking pages (via Bing), compares word count, keyword usage in title/H1, keyword density, and surfaces content-gap terms competitors cover that the page does not.
- **SEO score & recommendations** - a 0-100 score with prioritized (high/medium/low) actionable fixes.

## Run

```bash
pip install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5000, paste a page URL, optionally add a target keyword, and click **Analyze page**.

## Project structure

```
app.py                      Flask routes (/, /analyze)
analyzer/fetch.py           Page fetching and parsing
analyzer/onpage.py          On-page audit checks (incl. target keyword checks)
analyzer/keywords.py        Tokenization, keyword extraction, keyword usage stats
analyzer/competition.py     SERP scraping (Bing) and competitor comparison
analyzer/recommendations.py Score calculation and recommendation engine
templates/                  index.html (form), report.html (report)
static/style.css            Styling
```

## Notes

- Competitor search uses Bing's public HTML results; no API key is required. If scraping is blocked or a competitor page refuses bots, those entries are skipped gracefully.
- Keyword density guidance: roughly 0.5-2.5% for a target keyword is a healthy range; above 3% is flagged as potential stuffing.
