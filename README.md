# VeriWise
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/AryaMundra/VeriWise)

VeriWise is a full-stack web application designed to combat misinformation by detecting manipulated media (such as DeepFakes and AI-generated images) and verifying the factuality of textual claims. It integrates a Python and FastAPI backend for AI-powered analysis with a modern Next.js frontend for a seamless user experience.

## Features

-   **DeepFake & AI Media Detection:** Analyzes images and videos to identify manipulations and AI-generated content using specialized Transformer models. The video analysis inspects both visual frames and the audio track for a comprehensive verdict.
-   **Automated Fact-Checking:** Decomposes textual content into individual claims, assesses their check-worthiness, generates search queries, retrieves evidence from the web (via Serper), and verifies each claim using a large language model (Gemini).
-   **Bias Detection:** Assesses textual content for potential bias, classifying it as either "Neutral" or "Biased".
-   **Multimodal Input:** Accepts text, images, and videos. The backend can automatically transcribe media content to text for fact-checking.
-   **Interactive Chat Interface:** A user-friendly chat application where users can submit content and receive detailed analysis results in real-time.
-   **AI-Generated Summary:** Provides a concise, AI-generated summary of the overall analysis results, highlighting key findings and trustworthiness.

## Architecture

The application follows a client-server architecture:

-   **Frontend (Next.js):** A responsive web interface built with React and Tailwind CSS. It provides a landing page and a dedicated `/chat` page for users to upload files and submit text for analysis.
-   **Backend (Python/FastAPI):** A powerful API server that exposes a central `/api/analyze` endpoint. This endpoint receives multimodal input, orchestrates the analysis by running different modules concurrently, and returns a structured JSON response.
-   **AI Analysis Modules:**
    -   `AI_Image.py` & `Manipulated.py`: Handle AI-generated and manipulated image detection.
    -   `Deep_video.py`: Performs comprehensive deepfake analysis on videos, including audio.
    -   `fact_verify.py` & `factcheck/`: A sophisticated fact-checking pipeline that leverages the Gemini and Serper APIs for claim decomposition, evidence retrieval, and verification.
    -   `biasness.py`: Detects bias in text.

## Technologies Used

-   **Frontend:** Next.js, React, Tailwind CSS, Framer Motion
-   **Backend:** Python, FastAPI, Uvicorn
-   **AI & Data Processing:** PyTorch, Hugging Face Transformers, OpenCV, Librosa, MoviePy, Google Generative AI (Gemini), Serper API

## Installation

### 1. Backend Setup

To run the backend FastAPI server, follow these steps:

```bash
cd backend

python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Create a .env file in the `backend` directory and add your API keys:
# GEMINI_API_KEY=YOUR_GEMINI_KEY
# GEMINI_API_KEY_MEDIA=YOUR_GEMINI_KEY_FOR_MEDIA_PROCESSING
# SERPER_API_KEY=YOUR_SERPER_KEY
# You can add up to 5 Gemini keys (GEMINI_API_KEY_2, etc.) for parallel processing.

uvicorn main:app --reload
```
The backend will be running at `http://localhost:8000`.

### 2. Frontend Setup

To run the Next.js frontend, open a new terminal and follow these steps:

```bash
cd frontend

npm install

npm run dev
```
The frontend will be accessible at `http://localhost:3000`.

## Usage

1.  Ensure both the backend and frontend servers are running.
2.  Open your browser and navigate to `http://localhost:3000`.
3.  Click "Try Now" or navigate directly to `http://localhost:3000/chat`.
4.  In the chat interface, you can:
    -   Enter text into the input box.
    -   Click the image or video icon to upload a media file.
5.  Press `Enter` or click the `Send` button to submit your content for analysis.
6.  The results from the various AI modules will be displayed in the chat as a structured card.

## Test Data
The repository includes sample video files for testing the deepfake detection capabilities. You can find them in the `backend/DeepFake/Test_data/` directory.