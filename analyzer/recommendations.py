from .onpage import audit_page

WEIGHTS = {"fail": 12, "high": 12, "medium": 6, "warn": 6, "low": 2, "pass": 0}
SEVERITY_ORDER = {"high": 0, "fail": 0, "medium": 1, "warn": 1, "low": 2, "pass": 3}


def build_report(page, keyword, keywords, competition):
    audit = audit_page(page, keyword)
    recommendations = []

    for check in audit["checks"]:
        if check["status"] in ("pass",):
            continue
        recommendations.append(
            {
                "severity": check["status"],
                "title": check["name"],
                "detail": check["detail"],
            }
        )

    if keyword and competition and competition.get("summary"):
        recommendations.extend(_competition_recommendations(page, keyword, competition))

    recommendations.sort(key=lambda r: SEVERITY_ORDER.get(r["severity"], 3))

    score = 100
    for rec in recommendations:
        score -= WEIGHTS.get(rec["severity"], 0)
    score = max(0, min(100, score))

    passed = [c for c in audit["checks"] if c["status"] == "pass"]
    return {
        "score": score,
        "audit": audit,
        "keywords": keywords,
        "competition": competition,
        "recommendations": recommendations,
        "passed": passed,
    }


def _competition_recommendations(page, keyword, competition):
    summary = competition.get("summary", {})
    competitors = competition.get("competitors", [])
    recs = []
    if not summary:
        return recs

    our_words = len((page.get("body_text", "") or "").split())
    avg_words = summary.get("avg_word_count", 0)
    if avg_words and our_words < avg_words * 0.7:
        recs.append(
            {
                "severity": "medium",
                "title": "Content depth gap",
                "detail": (
                    f"Competitors ranking for \"{keyword}\" average {avg_words} words; "
                    f"this page has {our_words}. Expand the content toward the competitor average."
                ),
            }
        )

    pct_title = summary.get("pct_keyword_in_title", 0)
    if pct_title >= 60:
        recs.append(
            {
                "severity": "high",
                "title": "Competitors use the keyword in titles",
                "detail": f"{pct_title}% of top-ranking pages include \"{keyword}\" in their title tag. Match this to stay competitive.",
            }
        )

    pct_h1 = summary.get("pct_keyword_in_h1", 0)
    if pct_h1 >= 60:
        recs.append(
            {
                "severity": "medium",
                "title": "Competitors use the keyword in H1s",
                "detail": f"{pct_h1}% of top-ranking pages include \"{keyword}\" in their H1.",
            }
        )

    gaps = _content_gaps(page, competitors)
    if gaps:
        recs.append(
            {
                "severity": "low",
                "title": "Content gaps to cover",
                "detail": (
                    "Top competitors commonly cover terms this page does not: "
                    + ", ".join(f"\"{kw}\"" for kw in gaps[:8])
                    + ". Consider adding sections that address them."
                ),
            }
        )
    return recs


def _content_gaps(page, competitors, top=10):
    from .keywords import tokenize

    our_tokens = set(tokenize(page.get("body_text", "") or ""))
    our_phrases = {" ".join(pair) for pair in zip(sorted(our_tokens), sorted(our_tokens))}
    counter = {}
    for competitor in competitors:
        for kw in competitor["top_keywords"]:
            if " " in kw:
                covered = all(part in our_tokens for part in kw.split())
            else:
                covered = kw in our_tokens
            if covered:
                continue
            counter.setdefault(kw, 0)
            counter[kw] += 1
    return [kw for kw, _ in sorted(counter.items(), key=lambda item: -item[1])[:top]]
