from flask import Flask, render_template, request

from analyzer.competition import analyze_competition
from analyzer.fetch import fetch_page
from analyzer.keywords import extract_keywords
from analyzer.recommendations import build_report

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    url = (request.form.get("url") or "").strip()
    keyword = (request.form.get("keyword") or "").strip()

    if not url:
        return render_template("index.html", error="Enter a page URL to analyze.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        page = fetch_page(url)
    except Exception as exc:
        return render_template("index.html", error=f"Could not fetch {url}: {exc}")

    keywords = extract_keywords(page)
    competition = analyze_competition(keyword, exclude_url=url, limit=7) if keyword else None
    report = build_report(page, keyword or None, keywords, competition)
    return render_template(
        "report.html",
        report=report,
        page=page,
        url=url,
        keyword=keyword,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
