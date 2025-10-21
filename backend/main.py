# backend/main.py
import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import threading, time

# Load .env
load_dotenv()

from core import QueryGenerator, retriever, ClaimVerify
from utils import multimodal

# ✅ Import your deepfake detection modules
from DeepFake.Deep_video import CompleteDeepfakeDetector
from DeepFake.AI_Image import classify_image
from DeepFake.Manipulated import detect_deepfake


app = FastAPI(title="Multimodal FactCheck + Deepfake Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use '*' for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- FACT-CHECK ROUTE ---------------- #
class VerifyResponse(BaseModel):
    verdict: str
    score: float
    justification: str
    evidence: list


@app.post("/api/verify", response_model=VerifyResponse)
async def verify_claim(
    text_input: Optional[str] = Form(None),
    video: Optional[UploadFile] = File(None),
):
    video_path = None
    if video:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename)[1])
        with open(tmp.name, "wb") as f:
            shutil.copyfileobj(video.file, f)
        video_path = tmp.name

    # 1️⃣ Extract multimodal data
    multimodal_data = multimodal.multimodal_extract(video_path=video_path, text_input=text_input)
    combined_text = (
        (multimodal_data.get("text_input") or "") + "\n" + (multimodal_data.get("transcript") or "")
    ).strip()

    # 2️⃣ Generate factual search queries
    queries = QueryGenerator.generate_queries(combined_text)
    if not queries and multimodal_data.get("frames"):
        queries = ["Fact-check this video context"]

    # 3️⃣ Retrieve evidence using Serper
    evidence_groups = retriever.get_evidence(queries, top_k=3)
    flattened_evidence = [
        {"query": q["query"], "snippet": r.get("snippet"), "url": r.get("url")}
        for q in evidence_groups for r in q.get("results", [])
    ]

    # 4️⃣ Verify claim with Gemini
    claim_text = text_input or combined_text or "No Claim Provided"
    verification = ClaimVerify.gemini_verify_multimodal(
        claim_text,
        flattened_evidence,
        frames=multimodal_data.get("frames", []),
        transcript=multimodal_data.get("transcript", "")
    )

    return {
        "verdict": verification.get("verdict", "NOT_ENOUGH_INFO"),
        "score": float(verification.get("score", 0.0)),
        "justification": verification.get("justification", ""),
        "evidence": flattened_evidence,
    }


# ---------------- NEW DEEPFAKE DETECTION ROUTE ---------------- #
class DeepfakeResponse(BaseModel):
    type: str  # "image" or "video"
    prediction: str
    confidence: float
    details: Optional[dict] = None


# @app.post("/api/deepfake", response_model=DeepfakeResponse)


def delayed_delete(path, delay=2):
    """Delete a temporary file after a short delay."""
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[Cleanup] Deleted temp file: {path}")
        except Exception as e:
            print(f"[Cleanup Error] Could not delete {path}: {e}")
    threading.Thread(target=_delete, daemon=True).start()


@app.post("/api/deepfake", response_model=DeepfakeResponse)
async def detect_deepfake_api(
    file: UploadFile = File(...),
    media_type: str = Form(...),
):
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        with open(tmp.name, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_path = tmp.name

        # Run detection
        if media_type.lower() == "video":
            detector = CompleteDeepfakeDetector()
            results = detector.analyze_video(file_path, cleanup=True)
            verdict = results.get("overall_verdict", {}).get("verdict", "UNKNOWN")
            risk = results.get("overall_verdict", {}).get("risk_level", "UNKNOWN")

            return {
                "type": "video",
                "prediction": verdict,
                "confidence": 1.0 if risk == "HIGH" else 0.7 if risk == "MEDIUM" else 0.4,
                "details": results,
            }

        elif media_type.lower() == "image":
            ai_result = classify_image(file_path)
            df_result = detect_deepfake(file_path)

            combined_prediction = (
                "FAKE" if (ai_result["predicted_class"] == "Fake" or df_result["is_manipulated"]) else "REAL"
            )
            avg_conf = (ai_result["confidence"] + df_result["confidence"]) / 2

            return {
                "type": "image",
                "prediction": combined_prediction,
                "confidence": float(avg_conf),
                "details": {
                    "AI_image_model": ai_result,
                    "Manipulated_model": df_result,
                },
            }

        else:
            return {"type": "unknown", "prediction": "Invalid media_type", "confidence": 0.0}

    except Exception as e:
        return {
            "type": media_type,
            "prediction": "ERROR",
            "confidence": 0.0,
            "details": {"error": str(e)},
        }
    finally:
        delayed_delete(tmp.name)  # safely delete after short delay

