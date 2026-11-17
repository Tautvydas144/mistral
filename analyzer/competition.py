import base64
from collections import Counter
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .fetch import BROWSER_HEADERS, fetch_page
from .keywords import extract_keywords, keyword_usage

SEARCH_URL = "https://www.bing.com/search"


def search_competitors(query, limit=5):
    response = requests.get(
        SEARCH_URL,
        params={"q": query, "count": str(limit + 5)},
        headers=BROWSER_HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen = set()
    for anchor in soup.select("li.b_algo h2 a"):
        url = _decode_bing_url(anchor.get("href", ""))
        title = anchor.get_text(" ", strip=True)
        host = urlparse(url).netloc
        if not host or url in seen:
            continue
        seen.add(url)
        results.append({"title": title, "url": url})
        if len(results) >= limit:
            break
    return results


def analyze_competition(keyword, exclude_url=None, limit=5):
    try:
        results = search_competitors(keyword, limit=limit)
    except Exception as exc:
        return {"error": f"Could not fetch search results: {exc}", "competitors": []}

    exclude_host = urlparse(exclude_url or "").netloc.lower().removeprefix("www.")
    competitors = []
    for result in results:
        host = urlparse(result["url"]).netloc.lower().removeprefix("www.")
        if exclude_host and host == exclude_host:
            continue
        try:
            page = fetch_page(result["url"], timeout=12)
        except Exception:
            continue
        usage = keyword_usage(page, keyword)
        competitors.append(
            {
                "title": result["title"],
                "url": result["url"],
                "host": host,
                "word_count": len((page.get("body_text", "") or "").split()),
                "keyword_in_title": usage.get("in_title", False),
                "keyword_in_h1": usage.get("in_h1", False),
                "keyword_density": usage.get("density", 0.0),
                "top_keywords": [k["keyword"] for k in extract_keywords(page, limit=8)],
            }
        )
        if len(competitors) >= limit:
            break

    return {"competitors": competitors, "summary": _summarize(keyword, competitors)}


def _summarize(keyword, competitors):
    if not competitors:
        return {}
    count = len(competitors)
    return {
        "avg_word_count": round(sum(c["word_count"] for c in competitors) / count),
        "pct_keyword_in_title": round(100.0 * sum(c["keyword_in_title"] for c in competitors) / count),
        "pct_keyword_in_h1": round(100.0 * sum(c["keyword_in_h1"] for c in competitors) / count),
        "avg_density": round(sum(c["keyword_density"] for c in competitors) / count, 2),
        "common_keywords": _common_keywords(competitors),
    }


def _common_keywords(competitors, top=10):
    counter = Counter()
    for competitor in competitors:
        counter.update(set(competitor["top_keywords"]))
    return [
        {"keyword": kw, "pages": pages}
        for kw, pages in counter.most_common(top)
        if pages > 1
    ]


def _decode_bing_url(href):
    parsed = urlparse(href)
    if "bing.com" not in parsed.netloc:
        return href
    value = parse_qs(parsed.query).get("u", [None])[0]
    if not value or not value.startswith("a1"):
        return href
    encoded = value[2:]
    encoded += "=" * (-len(encoded) % 4)
    try:
        return base64.urlsafe_b64decode(encoded).decode("utf-8", "ignore")
    except Exception:
        return href
