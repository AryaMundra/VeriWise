# main.py
import os
import shutil
import tempfile
import traceback
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import importlib

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from concurrent.futures import ThreadPoolExecutor


# Logging setup
DEBUG_MODE = os.getenv("DEBUG", "0") in ("1", "true", "True")
logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("multimodal-backend")

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
# Dynamic import helpers
# -----------------------
def try_import(module_name: str):
    """
    Try importing module_name, return module object or (None, str(error_msg))
    """
    try:
        module = importlib.import_module(module_name)
        logger.debug(f"Imported module {module_name}")
        return module, None
    except Exception as e:
        tb = traceback.format_exc()
        logger.warning(f"Failed to import {module_name}: {e}")
        logger.debug(tb)
        return None, tb


# Attempt imports (capture exceptions for diagnostics)
bias_module, bias_err = try_import("biasness")
fact_module, fact_err = try_import("fact_verify")
ai_image_module, ai_image_err = try_import("AI_Image")
manipulated_module, manipulated_err = try_import("Manipulated")
deep_video_module, deep_video_err = try_import("Deep_video")

# Inspect which modules are available
AVAILABLE_MODULES = {
    "biasness": bias_module is not None,
    "fact_verify": fact_module is not None,
    "AI_Image": ai_image_module is not None,
    "Manipulated": manipulated_module is not None,
    "Deep_video": deep_video_module is not None,
}
logger.info(f"Available modules: {AVAILABLE_MODULES}")

# -----------------------
# Utility Helpers
# -----------------------

def save_uploadfile_to_temp(upload_file: UploadFile) -> str:
    """Save UploadFile to a temporary file and return path."""
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ""
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
        logger.debug(f"Saved upload to {tmp_path}")
    except Exception:
        logger.exception("Error while saving uploaded file")
        # If failed, remove file if created
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise
    finally:
        try:
            upload_file.file.close()
        except Exception:
            pass
    return tmp_path


async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


def module_missing_details():
    details = {}
    if bias_module is None:
        details["biasness"] = bias_err
    if fact_module is None:
        details["fact_verify"] = fact_err
    if ai_image_module is None:
        details["AI_Image"] = ai_image_err
    if manipulated_module is None:
        details["Manipulated"] = manipulated_err
    if deep_video_module is None:
        details["Deep_video"] = deep_video_err
    return details


# -----------------------
# Analysis Wrappers (guarded)
# -----------------------

def analyze_bias_text_sync(text: str) -> Dict[str, Any]:
    if bias_module is None:
        raise RuntimeError("biasness.py not available")
    label, score = bias_module.predict_bias(text)
    return {"label": label, "score": float(score)}


def run_factcheck_sync(input_text: Optional[str] = None, image_path: Optional[str] = None,
                       video_path: Optional[str] = None, text_file: Optional[str] = None) -> Dict[str, Any]:
    if fact_module is None:
        raise RuntimeError("fact_verify.py not available")
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
        raise RuntimeError("AI_Image.py not available")
    return ai_image_module.classify_image(image_path)


def detect_manipulated_sync(image_path: str) -> Dict[str, Any]:
    if manipulated_module is None:
        raise RuntimeError("Manipulated.py not available")
    return manipulated_module.detect_deepfake(image_path)


def analyze_video_sync(video_path: str) -> Dict[str, Any]:
    if deep_video_module is None:
        raise RuntimeError("Deep_video.py not available")
    detector = deep_video_module.CompleteDeepfakeDetector()
    results = detector.analyze_video(video_path, cleanup=True)
    return results


# -----------------------
# Gemini configuration (optional)
# -----------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        genai_available = True
    except Exception:
        logger.exception("Failed to import/configure google.generativeai")
        genai_available = False
else:
    genai_available = False


def generate_summary(analysis_results: Dict[str, Any]) -> str:
    if not genai_available:
        return "Gemini API key not configured or gemini client not available. Summary not available."

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            "You are an AI summarizer for a misinformation detection system. "
            "Given the following analysis results (including bias, deepfake, AI-generated content, etc.), "
            "write a short and direct summary describing what the analysis indicates. "
            "Focus only on whether the content appears trustworthy or manipulated. "
            "Be factual, neutral, and limit to 3 concise sentences.\n\n"
            f"Analysis results:\n{analysis_results}"
        )
        response = model.generate_content(prompt)
        return response.text.strip() if response and getattr(response, "text", None) else "No summary generated."
    except Exception:
        logger.exception("Gemini summary generation failed")
        return "Error generating summary."


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

    # Provide debug info about missing modules (but do not instantly abort if some are missing)
    missing_details = module_missing_details()
    logger.debug(f"Missing module details: {list(missing_details.keys())}")

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

        # Build tasks conditionally depending on which modules are available
        tasks = []
        # Keep track of which keys we expect back
        expected = {}

        # Case: text + image
        if text and image_path:
            if AVAILABLE_MODULES["biasness"]:
                tasks.append(run_in_thread(analyze_bias_text_sync, text))
                expected["bias"] = True
            if AVAILABLE_MODULES["fact_verify"]:
                tasks.append(run_in_thread(run_factcheck_sync, text, image_path))
                expected["factcheck"] = True
            if AVAILABLE_MODULES["AI_Image"]:
                tasks.append(run_in_thread(classify_image_sync, image_path))
                expected["ai_image"] = True
            if AVAILABLE_MODULES["Manipulated"]:
                tasks.append(run_in_thread(detect_manipulated_sync, image_path))
                expected["manipulated"] = True

            if not tasks:
                # nothing available to run
                return JSONResponse(status_code=500, content={
                    "error": "No analysis modules are available on the server.",
                    "missing_modules": list(missing_details.keys()),
                    "hint": "Set up the missing python modules or run with DEBUG=1 to inspect import failures."
                })

            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            # assign in the same order as expected keys
            idx = 0
            if expected.get("bias"):
                val = gathered[idx]; idx += 1
                results["bias"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("factcheck"):
                val = gathered[idx]; idx += 1
                results["factcheck"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("ai_image"):
                val = gathered[idx]; idx += 1
                results["ai_image"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("manipulated"):
                val = gathered[idx]; idx += 1
                results["manipulated"] = val if not isinstance(val, Exception) else {"error": str(val)}

        # Case: text only
        elif text and not image_path and not video_path:
            if AVAILABLE_MODULES["biasness"]:
                tasks.append(run_in_thread(analyze_bias_text_sync, text))
                expected["bias"] = True
            if AVAILABLE_MODULES["fact_verify"]:
                tasks.append(run_in_thread(run_factcheck_sync, text, None))
                expected["factcheck"] = True

            if not tasks:
                return JSONResponse(status_code=500, content={
                    "error": "No text analysis modules available.",
                    "missing_modules": list(missing_details.keys())
                })

            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            idx = 0
            if expected.get("bias"):
                val = gathered[idx]; idx += 1
                results["bias"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("factcheck"):
                val = gathered[idx]; idx += 1
                results["factcheck"] = val if not isinstance(val, Exception) else {"error": str(val)}

        # Case: image only
        elif image_path and not text and not video_path:
            if AVAILABLE_MODULES["fact_verify"]:
                tasks.append(run_in_thread(run_factcheck_sync, None, image_path))
                expected["factcheck"] = True
            if AVAILABLE_MODULES["AI_Image"]:
                tasks.append(run_in_thread(classify_image_sync, image_path))
                expected["ai_image"] = True
            if AVAILABLE_MODULES["Manipulated"]:
                tasks.append(run_in_thread(detect_manipulated_sync, image_path))
                expected["manipulated"] = True

            if not tasks:
                return JSONResponse(status_code=500, content={
                    "error": "No image analysis modules available.",
                    "missing_modules": list(missing_details.keys())
                })

            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            idx = 0
            if expected.get("factcheck"):
                val = gathered[idx]; idx += 1
                results["factcheck"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("ai_image"):
                val = gathered[idx]; idx += 1
                results["ai_image"] = val if not isinstance(val, Exception) else {"error": str(val)}
            if expected.get("manipulated"):
                val = gathered[idx]; idx += 1
                results["manipulated"] = val if not isinstance(val, Exception) else {"error": str(val)}

        # Case: video present
        elif video_path:
            if AVAILABLE_MODULES["Deep_video"]:
                video_res = await run_in_thread(analyze_video_sync, video_path)
                results["video"] = video_res
            else:
                results["video"] = {"error": "Deep_video module not available."}

            # try factcheck against video if available
            if AVAILABLE_MODULES["fact_verify"]:
                try:
                    fact_res = await run_in_thread(run_factcheck_sync, None, None, video_path)
                    results["factcheck"] = fact_res
                except Exception as e:
                    results["factcheck"] = {"error": str(e)}
        else:
            raise HTTPException(status_code=400, detail="Unsupported combination of inputs.")

        # Try generate summary if genai available
        try:
            results["summary"] = generate_summary(results) if genai_available else "No summary (gemini not configured)."
        except Exception:
            logger.exception("Summary generation failed")
            results["summary"] = "Summary generation failed."
        print(results)
        logger.info("Analysis completed, returning results.")
        return JSONResponse(status_code=200, content={"status": "ok", "results": results, "missing_modules": list(missing_details.keys())})

    except Exception as e:
        logger.exception("Unhandled exception during /api/analyze")
        tb = traceback.format_exc()
        # If debug, return traceback in response for easier dev debugging
        if DEBUG_MODE:
            return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb, "missing_modules": list(missing_details.keys())})
        else:
            return JSONResponse(status_code=500, content={"error": "Internal server error", "missing_modules": list(missing_details.keys())})
    finally:
        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass


@app.get("/api/health")
async def health():
    missing = list(module_missing_details().keys())
    return {"status": "ok", "missing_modules": missing, "has_frontend": FRONTEND_PATH.exists()}


@app.get("/api/download/")
async def download_test(filepath: str):
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)


@app.on_event("startup")
async def startup_event():
    logger.info("=== Multimodal FastAPI backend starting ===")
    logger.info("Ensure required modules and keys are configured properly.")
    logger.debug(f"Module availability: {AVAILABLE_MODULES}")
