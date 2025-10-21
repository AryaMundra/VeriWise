# backend/core/QueryGenerator.py
import re
from typing import List

def split_into_sentences(text: str):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

def key_phrases_from_sentence(sent):
    stop = {"which","that","where","what","when","who","the","a","an","is","are","was","were","in","on","of","and","or"}
    tokens = re.findall(r"[A-Za-z0-9\-]+", sent)
    return [t for t in tokens if len(t) > 4 and t.lower() not in stop][:6]

def generate_queries(text_or_transcript: str, max_queries=5) -> List[str]:
    if not text_or_transcript:
        return []
    queries, seen = [], set()
    for s in split_into_sentences(text_or_transcript):
        if len(queries) >= max_queries:
            break
        kws = key_phrases_from_sentence(s)
        for q in [s[:240], " ".join(kws)]:
            if q and q not in seen:
                queries.append(q)
                seen.add(q)
    return queries

