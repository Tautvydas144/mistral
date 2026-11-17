import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'’\-]+")

STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and",
    "any", "are", "aren", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did",
    "do", "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "will", "with",
    "would", "you", "your", "yours", "yourself", "yourselves", "get", "got",
    "one", "two", "use", "used", "using", "also", "may", "many", "much", "new",
    "like", "make", "made", "see", "way", "well", "even", "back", "still",
    "please", "via", "per", "click", "here", "read", "learn", "home", "page",
    "site", "website", "privacy", "policy", "terms", "cookie", "cookies",
    "menu", "search", "subscribe", "email", "login", "sign", "share", "post",
    "posted", "comment", "comments", "reply", "skip", "content", "toggle",
}


def tokenize(text):
    return [
        t for t in (m.group(0).lower().strip("’'-") for m in TOKEN_RE.finditer(text))
        if len(t) > 2 and t not in STOPWORDS
    ]


def extract_keywords(page, limit=15):
    weighted_fields = [
        ("title", 8.0),
        ("meta_description", 4.0),
        ("h1", 5.0),
        ("h2", 3.0),
        ("h3", 2.0),
        ("body_text", 1.0),
    ]

    scores = Counter()
    counts = Counter()
    for field, weight in weighted_fields:
        tokens = tokenize(page.get(field, "") or "")
        counts.update(tokens)
        scores.update({token: weight for token in tokens})

    body_tokens = tokenize(page.get("body_text", "") or "")
    title_tokens = set(tokenize(page.get("title", "") or ""))
    h1_tokens = set(tokenize(" ".join(page.get("headings", {}).get("h1", []))))
    bigrams = Counter(zip(body_tokens, body_tokens[1:]))
    total_tokens = max(len(body_tokens), 1)

    keywords = []
    for token, count in counts.most_common(limit * 2):
        if count < 2:
            continue
        keywords.append(
            {
                "keyword": token,
                "count": count,
                "density": round(100.0 * count / total_tokens, 2),
                "score": round(scores[token], 1),
            }
        )

    for (w1, w2), count in bigrams.most_common(limit * 2):
        if count < 2:
            continue
        phrase = f"{w1} {w2}"
        bonus = 3.0 * (phrase in " ".join(title_tokens)) + 3.0 * (phrase in " ".join(h1_tokens))
        if not bonus and count < 3:
            continue
        bigram_score = count + bonus * 2
        keywords.append(
            {
                "keyword": phrase,
                "count": count,
                "density": round(100.0 * count / total_tokens, 2),
                "score": round(bigram_score, 1),
            }
        )

    keywords.sort(key=lambda k: k["score"], reverse=True)
    return keywords[:limit]


def keyword_usage(page, keyword):
    keyword = keyword.lower().strip()
    if not keyword:
        return {}
    body_tokens = tokenize(page.get("body_text", "") or "")
    tokens = keyword.split()
    if len(tokens) == 1:
        occurrences = body_tokens.count(keyword)
    else:
        joined = " ".join(body_tokens)
        occurrences = joined.count(keyword)
    total = max(len(body_tokens), 1)
    headings = page.get("headings", {})
    return {
        "in_title": keyword in (page.get("title", "") or "").lower(),
        "in_description": keyword in (page.get("meta_description", "") or "").lower(),
        "in_h1": any(keyword in h.lower() for h in headings.get("h1", [])),
        "in_h2": any(keyword in h.lower() for h in headings.get("h2", [])),
        "in_url": keyword.replace(" ", "-") in (page.get("final_url", "") or "").lower(),
        "in_first_200_words": keyword in " ".join(body_tokens[:60]),
        "occurrences": occurrences,
        "density": round(100.0 * occurrences / total, 2),
    }
