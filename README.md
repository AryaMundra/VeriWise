# VeriWise 

VeriWise is a **full-stack web application** designed to detect manipulated media (DeepFakes) and verify textual claims using AI. It combines **Next.js** for the frontend and **Python-based AI services** for the backend to provide a seamless fact-checking and media verification experience.


## Features

- **DeepFake Detection**: Detect manipulated images and videos.
- **Fact-Checking**: Verify textual claims with evidence retrieval.
- **Multimodal Input Support**: Process text, images, and videos.
- **Interactive Web Interface**: Upload media and get verification results in real-time.


## Architecture

[Browser] --> [Next.js Frontend] --> [Backend API (main.py)]
--> [DeepFake Service: AI_Image.py, Deep_video.py]
--> [Fact-Check Service: ClaimVerify.py, QueryGenerator.py, retriever.py]
--> [Multimodal Utils: multimodal.py]


- **Frontend**: Next.js for UI, routing, and media uploads.
- **Backend**: FastAPI exposes endpoints for:
  - DeepFake detection
  - Fact-checking via claim verification
  - Multimodal input processing
- **AI Modules**: Modular design ensures DeepFake detection and Fact-Check services are independent and reusable.
- **Data Flow**: Uploaded media → Backend API → Appropriate AI module → JSON response → Frontend display.


## Installation

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload  # Run FastAPI server
````

### Frontend

```bash
cd frontend
npm install
npm run dev
```


## Usage

1. Open the frontend in your browser (`http://localhost:3000`).
2. Navigate to:

   * **DeepFake Detection** → Upload image/video for analysis.
   * **Fact-Check** → Enter a claim to verify against sources.
3. View results instantly in the dashboard.


## Technologies

* **Frontend**: Next.js, Tailwind CSS
* **Backend**: Python, FastAPI
* **DeepFake Detection**: OpenCV, PyTorch, Librosa, Hugging Face Transformers
* **Fact-Checking**: Gemini, Serper
* **Multimodal Preprocessing**: Shared utilities for text, image, and video inputs


## Test Data

* `backend/DeepFake/Test_data/` contains sample videos and images to test DeepFake detection.


## Links

* **GitHub Repo**: [VeriWise](https://github.com/aryamundra/veriwise)


## Future Improvements

* Support **real-time video streams**.
* Integrate **external knowledge bases** for improved fact-checking.
* Deploy as a **full-stack cloud application** with scalable AI inference.