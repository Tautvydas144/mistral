def audit_page(page, keyword=None):
    checks = []
    facts = {}

    title = page.get("title", "")
    if not title:
        checks.append(_check("fail", "Title tag", "No <title> tag found."))
    elif len(title) < 30:
        checks.append(_check("warn", "Title tag", f"Title is short ({len(title)} chars). Aim for 30-60."))
    elif len(title) > 60:
        checks.append(_check("warn", "Title tag", f"Title is long ({len(title)} chars) and may be truncated. Aim for 30-60."))
    else:
        checks.append(_check("pass", "Title tag", f"Good length ({len(title)} chars)."))

    description = page.get("meta_description", "")
    if not description:
        checks.append(_check("fail", "Meta description", "No meta description found."))
    elif len(description) < 70:
        checks.append(_check("warn", "Meta description", f"Description is short ({len(description)} chars). Aim for 70-160."))
    elif len(description) > 160:
        checks.append(_check("warn", "Meta description", f"Description is long ({len(description)} chars) and will be truncated. Aim for 70-160."))
    else:
        checks.append(_check("pass", "Meta description", f"Good length ({len(description)} chars)."))

    h1s = page.get("headings", {}).get("h1", [])
    if len(h1s) == 0:
        checks.append(_check("fail", "H1 heading", "No H1 heading found."))
    elif len(h1s) > 1:
        checks.append(_check("warn", "H1 heading", f"{len(h1s)} H1 headings found; use exactly one."))
    else:
        checks.append(_check("pass", "H1 heading", f"Exactly one H1: \"{h1s[0][:70]}\""))

    h2s = page.get("headings", {}).get("h2", [])
    if len(h2s) == 0:
        checks.append(_check("warn", "Subheadings", "No H2 headings; add structure with H2/H3 sections."))
    else:
        checks.append(_check("pass", "Subheadings", f"{len(h2s)} H2 and {len(page.get('headings', {}).get('h3', []))} H3 headings."))

    word_count = _word_count(page.get("body_text", ""))
    facts["word_count"] = word_count
    if word_count < 150:
        checks.append(_check("fail", "Content length", f"Only {word_count} words of body text."))
    elif word_count < 300:
        checks.append(_check("warn", "Content length", f"{word_count} words; top-ranking pages usually have 300+."))
    else:
        checks.append(_check("pass", "Content length", f"{word_count} words of body text."))

    images_total = page.get("images_total", 0)
    missing_alt = page.get("images_missing_alt", [])
    facts["images_missing_alt"] = len(missing_alt)
    if images_total and len(missing_alt) == images_total:
        checks.append(_check("fail", "Image alt text", f"All {images_total} images are missing alt text."))
    elif missing_alt:
        checks.append(_check("warn", "Image alt text", f"{len(missing_alt)} of {images_total} images missing alt text."))
    else:
        checks.append(_check("pass", "Image alt text", f"All {images_total} images have alt text."))

    links = page.get("links_internal", 0) + page.get("links_external", 0)
    if links == 0:
        checks.append(_check("warn", "Links", "No links found on the page."))
    else:
        checks.append(_check(
            "pass",
            "Links",
            f"{page.get('links_internal', 0)} internal, {page.get('links_external', 0)} external.",
        ))

    if not page.get("canonical"):
        checks.append(_check("low", "Canonical URL", "No canonical tag; add one to prevent duplicate-content issues."))
    else:
        checks.append(_check("pass", "Canonical URL", page["canonical"][:80]))

    if not page.get("viewport"):
        checks.append(_check("fail", "Mobile viewport", "No viewport meta tag; page is not mobile-ready."))
    else:
        checks.append(_check("pass", "Mobile viewport", "Viewport meta tag present."))

    if not page.get("https"):
        checks.append(_check("fail", "HTTPS", "Page is served over plain HTTP."))
    else:
        checks.append(_check("pass", "HTTPS", "Secure connection."))

    if "noindex" in page.get("meta_robots", ""):
        checks.append(_check("fail", "Indexability", "Page has noindex; search engines will not index it."))
    else:
        checks.append(_check("pass", "Indexability", "No noindex directive found."))

    if not page.get("og"):
        checks.append(_check("low", "Social tags", "No Open Graph tags; shares will look plain on social media."))
    else:
        checks.append(_check("pass", "Social tags", f"{len(page['og'])} Open Graph tags present."))

    if not page.get("lang"):
        checks.append(_check("low", "Language", "No lang attribute on <html>."))
    else:
        checks.append(_check("pass", "Language", f"lang=\"{page['lang']}\""))

    size_kb = page.get("html_size_kb", 0)
    if size_kb > 500:
        checks.append(_check("warn", "Page size", f"HTML is {size_kb} KB; consider trimming."))
    else:
        checks.append(_check("pass", "Page size", f"HTML is {size_kb} KB."))

    if keyword:
        checks.extend(_keyword_checks(page, keyword))

    return {"checks": checks, "facts": facts}


def _keyword_checks(page, keyword):
    from .keywords import keyword_usage

    usage = keyword_usage(page, keyword)
    checks = []
    if not usage["in_title"]:
        checks.append(_check("high", f"Keyword in title", "\"{kw}\" is not in the title tag.".format(kw=keyword)))
    else:
        checks.append(_check("pass", f"Keyword in title", "Target keyword is in the title."))

    if not usage["in_h1"]:
        checks.append(_check("medium", "Keyword in H1", "Target keyword is not in the H1."))
    else:
        checks.append(_check("pass", "Keyword in H1", "Target keyword is in the H1."))

    if not usage["in_description"]:
        checks.append(_check("medium", "Keyword in meta description", "Target keyword is not in the meta description."))
    else:
        checks.append(_check("pass", "Keyword in meta description", "Target keyword is in the meta description."))

    if not usage["in_first_200_words"]:
        checks.append(_check("medium", "Keyword in intro", "Target keyword does not appear in the first ~200 words."))
    else:
        checks.append(_check("pass", "Keyword in intro", "Target keyword appears early in the content."))

    density = usage["density"]
    if density < 0.3:
        checks.append(_check("medium", "Keyword density", f"Density is {density}% ({usage['occurrences']} uses); too low for a target keyword."))
    elif density > 3.0:
        checks.append(_check("high", "Keyword density", f"Density is {density}%; this looks like keyword stuffing. Reduce usage."))
    else:
        checks.append(_check("pass", "Keyword density", f"Density is {density}% ({usage['occurrences']} uses) - healthy range."))

    return checks


def _word_count(text):
    return len(text.split())


def _check(status, name, detail):
    return {"status": status, "name": name, "detail": detail}
