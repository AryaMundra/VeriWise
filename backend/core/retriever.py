import os
import requests
import re

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

UNSAFE_KEYWORDS = {"porn", "sex", "nude", "xxx", "adult", "escort", "naked", "redtube"}

def is_safe_result(text_or_url: str) -> bool:
    text_or_url = text_or_url.lower()
    return not any(word in text_or_url for word in UNSAFE_KEYWORDS)


def serper_search(query, top_k=3):
    if not SERPER_API_KEY:
        return [{"source": "mock", "snippet": f"Mock result for '{query}'", "url": "https://example.com"}]

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        j = r.json()
        results = []
        for item in j.get("organic", [])[:top_k * 2]:  # oversample before filtering
            snippet = item.get("snippet") or item.get("title") or ""
            link = item.get("link") or ""
            if not is_safe_result(snippet) or not is_safe_result(link):
                print(f"[retriever] filtered adult/unsafe result for query='{query}' url={link}")
                continue
            results.append({
                "source": item.get("source", "web"),
                "snippet": snippet,
                "url": link
            })
            if len(results) >= top_k:
                break
        if not results:
            return [{"source": "mock", "snippet": f"No safe results for '{query}'", "url": "https://example.com"}]
        return results
    except Exception as e:
        print("serper error:", e)
        return [{"source": "mock", "snippet": f"Search error for '{query}'", "url": "https://example.com"}]


def get_evidence(queries, top_k=3):
    all_evidence = []
    for q in queries:
        ev = serper_search(q, top_k=top_k)
        all_evidence.append({"query": q, "results": ev})
    return all_evidence
