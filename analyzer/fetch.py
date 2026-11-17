import time

import requests
from bs4 import BeautifulSoup

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url, timeout=20):
    start = time.monotonic()
    response = requests.get(
        url, headers=BROWSER_HEADERS, timeout=timeout, allow_redirects=True
    )
    load_time = round(time.monotonic() - start, 2)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page = _parse(soup, url, response, load_time)
    return page


def _parse(soup, url, response, load_time):
    title_tag = soup.find("title")
    meta_description = soup.find("meta", attrs={"name": "description"})
    meta_robots = soup.find("meta", attrs={"name": "robots"})
    viewport = soup.find("meta", attrs={"name": "viewport"})
    canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    html_tag = soup.find("html")

    og = {}
    for tag in soup.find_all("meta", attrs={"property": True}):
        prop = tag.get("property", "")
        if prop.startswith("og:"):
            og[prop] = tag.get("content", "")

    headings = {}
    for level in range(1, 7):
        headings[f"h{level}"] = [
            h.get_text(" ", strip=True) for h in soup.find_all(f"h{level}")
        ]

    for tag in soup(["script", "style", "noscript", "svg", "iframe", "template",
                     "nav", "header", "footer", "aside", "form", "button"]):
        tag.decompose()
    body = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find(id="content")
        or soup.find("body")
    )
    body_text = body.get_text(" ", strip=True) if body else soup.get_text(" ", strip=True)

    images = soup.find_all("img")
    missing_alt = [
        img.get("src", "")[:120]
        for img in images
        if not (img.get("alt") or "").strip()
    ]

    internal = external = 0
    base_host = _host(url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if href.startswith("http"):
            if _host(href) == base_host:
                internal += 1
            else:
                external += 1
        else:
            internal += 1

    return {
        "url": url,
        "final_url": response.url,
        "status_code": response.status_code,
        "https": response.url.startswith("https://"),
        "load_time": load_time,
        "html_size_kb": round(len(response.content) / 1024, 1),
        "title": title_tag.get_text(" ", strip=True) if title_tag else "",
        "meta_description": (meta_description.get("content", "").strip() if meta_description else ""),
        "meta_robots": (meta_robots.get("content", "").strip().lower() if meta_robots else ""),
        "viewport": bool(viewport),
        "canonical": (canonical.get("href", "").strip() if canonical else ""),
        "lang": (html_tag.get("lang", "").strip() if html_tag else ""),
        "og": og,
        "headings": headings,
        "body_text": body_text,
        "images_total": len(images),
        "images_missing_alt": missing_alt,
        "links_internal": internal,
        "links_external": external,
    }


def _host(url):
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower().removeprefix("www.")
