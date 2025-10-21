import os
import re
import json
import base64
from typing import List

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)


def simple_heuristic_verify(claim: str, evidence_list: List[dict]):
    claim_tokens = set(re.findall(r"[A-Za-z0-9]+", claim.lower()))
    total_matches = 0
    checked = []
    for ev in evidence_list:
        snippet = ev.get("snippet", "")
        sn_tokens = set(re.findall(r"[A-Za-z0-9]+", snippet.lower()))
        matches = claim_tokens.intersection(sn_tokens)
        if matches:
            checked.append({
                "snippet": snippet,
                "matches": list(matches),
                "match_count": len(matches)
            })
            total_matches += len(matches)
    score = total_matches / (len(claim_tokens) + 1)
    if score > 0.2:
        verdict = "SUPPORTED"
    elif score > 0.05:
        verdict = "MIXED"
    else:
        verdict = "NOT_ENOUGH_INFO"
    justification = f"Heuristic overlap score={score*100:.2f}%."
    return {"verdict": verdict, "score": score, "justification": justification, "checked": checked}


def gemini_verify_multimodal(claim: str, evidence_list: List[dict], frames=None, transcript=None):
    """
    Multimodal verification using Gemini 2.5 models (supports text + images).
    """
    if not GEMINI_API_KEY:
        return simple_heuristic_verify(claim, evidence_list)

    evid_texts = []
    for ev in evidence_list:
        if "porn" in ev.get("url", "").lower():
            continue  # filter out NSFW
        evid_texts.append(f"- {ev.get('snippet','')} (source: {ev.get('url','')})")

    # Base instruction
    prompt = f"""
You are a professional fact-checker. Determine whether this claim is true, false, or unverifiable based on the provided textual and visual evidence.
Respond in **pure JSON** format with keys:
- verdict: SUPPORTED, REFUTED, or NOT_ENOUGH_INFO
- score: float (0 to 1)
- justification: 1–2 sentence reasoning

Claim:
\"\"\"{claim}\"\"\"

Text Evidence:
{chr(10).join(evid_texts)}
"""

    # Prepare parts for multimodal input
    parts = [{"text": prompt}]
    if frames:
        for frame in frames[:4]:  # Limit to first 4 frames
            _, buffer = cv2.imencode(".jpg", frame)
            b64_bytes = base64.b64encode(buffer).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_bytes
                }
            })

    # Try preferred models
    models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
    for model_name in models:
        try:
            print(f"[ClaimVerify] attempting model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([{"role": "user", "parts": parts}])
            text = response.text.strip()
            m = re.search(r'\{.*\}', text, re.S)
            if m:
                data = json.loads(m.group(0))
                return data
            else:
                return {"verdict": "NOT_ENOUGH_INFO", "score": 0.0, "justification": text}
        except Exception as e:
            print(f"[ClaimVerify] model {model_name} failed: {e}")

    print("[ClaimVerify] All Gemini models failed; using heuristic fallback.")
    return simple_heuristic_verify(claim, evidence_list)


def openai_verify(claim: str, evidence_list: List[dict], frames=None):
    return gemini_verify_multimodal(claim, evidence_list, frames)
