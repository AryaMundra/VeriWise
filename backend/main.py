import os
import shutil
import tempfile
import traceback
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from concurrent.futures import ThreadPoolExecutor

# Try to import provided analysis modules
try:
    import biasness as bias_module
except Exception:
    bias_module = None

try:
    import fact_verify as fact_module
except Exception:
    fact_module = None

try:
    import AI_Image as ai_image_module
except Exception:
    ai_image_module = None

try:
    import Manipulated as manipulated_module
except Exception:
    manipulated_module = None

try:
    import Deep_video as deep_video_module
except Exception:
    deep_video_module = None

app = FastAPI(title="Multimodal Analysis Backend (Hackathon)", version="1.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend if built
FRONTEND_PATH = Path("frontend/build")
if FRONTEND_PATH.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_PATH), html=True), name="frontend")

# ThreadPool for blocking CPU-bound ops
executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)


# -----------------------
# Utility Helpers
# -----------------------

def save_uploadfile_to_temp(upload_file: UploadFile) -> str:
    """Save UploadFile to a temporary file and return path."""
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ""
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return tmp_path


async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


def safe_import_check():
    missing = []
    if bias_module is None:
        missing.append("biasness.py")
    if fact_module is None:
        missing.append("fact_verify.py")
    if ai_image_module is None:
        missing.append("AI_Image.py")
    if manipulated_module is None:
        missing.append("Manipulated.py")
    if deep_video_module is None:
        missing.append("Deep_Video.py")
    return missing


# -----------------------
# Analysis Wrappers
# -----------------------

def analyze_bias_text_sync(text: str) -> Dict[str, Any]:
    if bias_module is None:
        raise RuntimeError("biasness.py not available / failed to import")
    label, score = bias_module.predict_bias(text)
    return {"label": label, "score": float(score)}


def run_factcheck_sync(input_text: Optional[str] = None, image_path: Optional[str] = None,
                       video_path: Optional[str] = None, text_file: Optional[str] = None) -> Dict[str, Any]:
    if fact_module is None:
        raise RuntimeError("fact_verify.py not available / failed to import")
    app_fc = fact_module.FactCheckApp()
    results = app_fc.process_input(
        input_text=input_text,
        text_file=text_file,
        audio_file=None,
        image_file=image_path,
        video_file=video_path
    )
    return results


def classify_image_sync(image_path: str) -> Dict[str, Any]:
    if ai_image_module is None:
        raise RuntimeError("AI_Image.py not available / failed to import")
    return ai_image_module.classify_image(image_path)


def detect_manipulated_sync(image_path: str) -> Dict[str, Any]:
    if manipulated_module is None:
        raise RuntimeError("Manipulated.py not available / failed to import")
    return manipulated_module.detect_deepfake(image_path)


def analyze_video_sync(video_path: str) -> Dict[str, Any]:
    if deep_video_module is None:
        raise RuntimeError("Deep_Video.py not available / failed to import")
    detector = deep_video_module.CompleteDeepfakeDetector()
    results = detector.analyze_video(video_path, cleanup=True)
    return results


# -----------------------
# API Endpoints
# -----------------------

@app.post("/api/analyze")
async def analyze(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
):
    """
    Main analysis endpoint.
    Accepts multipart form:
      - text: optional
      - image: optional
      - video: optional
    At least one input must be provided.
    """

    missing = safe_import_check()
    if missing:
        return JSONResponse(status_code=500, content={"error": "Missing required analysis modules", "missing": missing})

    if not text and image is None and video is None:
        raise HTTPException(status_code=400, detail="At least one of text, image, or video must be provided.")

    tmp_files = []
    image_path = None
    video_path = None

    try:
        if image:
            image_path = save_uploadfile_to_temp(image)
            tmp_files.append(image_path)
        if video:
            video_path = save_uploadfile_to_temp(video)
            tmp_files.append(video_path)

        results: Dict[str, Any] = {}
        results["text"] = text

        # -----------------------
        # Run modules in parallel
        # -----------------------

        if text and image_path:
            tasks = [
                run_in_thread(analyze_bias_text_sync, text),
                run_in_thread(run_factcheck_sync, text, image_path),
                run_in_thread(classify_image_sync, image_path),
                run_in_thread(detect_manipulated_sync, image_path),
            ]
            bias_res, fact_res, ai_res, manip_res = await asyncio.gather(*tasks)
            results.update({
                "bias": bias_res,
                "factcheck": fact_res,
                "ai_image": ai_res,
                "manipulated": manip_res
            })

        elif text and not image_path and not video_path:
            tasks = [
                run_in_thread(analyze_bias_text_sync, text),
                run_in_thread(run_factcheck_sync, text, None),
            ]
            bias_res, fact_res = await asyncio.gather(*tasks)
            results.update({
                "bias": bias_res,
                "factcheck": fact_res
            })

        elif image_path and not text and not video_path:
            tasks = [
                run_in_thread(run_factcheck_sync, None, image_path),
                run_in_thread(classify_image_sync, image_path),
                run_in_thread(detect_manipulated_sync, image_path),
            ]
            fact_res, ai_res, manip_res = await asyncio.gather(*tasks)
            results.update({
                "factcheck": fact_res,
                "ai_image": ai_res,
                "manipulated": manip_res
            })

        elif video_path:
            video_res = await run_in_thread(analyze_video_sync, video_path)
            try:
                fact_res = await run_in_thread(run_factcheck_sync, None, None, video_path)
            except Exception:
                fact_res = None
            results.update({
                "video": video_res,
                "factcheck": fact_res
            })

        else:
            raise HTTPException(status_code=400, detail="Unsupported combination of inputs.")

        return JSONResponse(status_code=200, content={"status": "ok", "results": results})

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass


@app.get("/api/health")
async def health():
    missing = safe_import_check()
    return {"status": "ok", "missing_modules": missing, "has_frontend": FRONTEND_PATH.exists()}


@app.get("/api/download/")
async def download_test(filepath: str):
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)


@app.on_event("startup")
async def startup_event():
    print("=== Multimodal FastAPI backend starting ===")
    print("Ensure all required modules and keys are configured properly.")
