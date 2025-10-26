
import google.generativeai as genai
import cv2
import base64
import os
from pathlib import Path
from typing import Optional, Union
from .logger import CustomLogger

logger = CustomLogger(__name__).getlog()


def voice2text(input_path: str, gemini_key: str) -> str:
    """
    Convert audio/speech to text using Gemini's audio understanding.
    
    Gemini can directly process audio files for transcription.
    Supports: MP3, WAV, FLAC, AAC, OGG, OPUS
    
    Args:
        input_path: Path to audio file
        gemini_key: Gemini API key
        
    Returns:
        Transcribed text from audio
    """
    try:
        # Configure Gemini
        genai.configure(api_key=gemini_key)
        
        # Upload audio file to Gemini
        logger.info(f"Uploading audio file: {input_path}")
        audio_file = genai.upload_file(path=input_path)
        
        # Wait for file to be processed
        import time
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name == "FAILED":
            raise ValueError(f"Audio file processing failed: {audio_file.state.name}")
        
        # Create model and generate transcription
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        prompt = "Generate a complete and accurate transcript of the speech in this audio file. Only return the transcript text without any additional commentary."
        
        response = model.generate_content([prompt, audio_file])
        
        # Clean up uploaded file
        genai.delete_file(audio_file.name)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error in voice2text: {str(e)}")
        raise


def image2text(input_path: str, gemini_key: str) -> str:
    """
    Generate description of an image using Gemini's vision capabilities.
    
    Gemini can directly process images without base64 encoding.
    Supports: PNG, JPEG, WEBP, HEIC, HEIF
    
    Args:
        input_path: Path to image file
        gemini_key: Gemini API key
        
    Returns:
        Description of the image
    """
    try:
        # Configure Gemini
        genai.configure(api_key=gemini_key)
        
        # Upload image file
        logger.info(f"Uploading image file: {input_path}")
        image_file = genai.upload_file(path=input_path)
        
        # Create model
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        prompt = "Please return the text mentioned in the image . If you find no text just return None ."
        
        response = model.generate_content([prompt, image_file])
        
        # Clean up uploaded file
        genai.delete_file(image_file.name)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error in image2text: {str(e)}")
        raise


def video2text(input_path: str, gemini_key: str) -> str:
    """
    Generate description of a video using Gemini's video understanding.
    
    Gemini can natively process video files without frame extraction.
    Supports: MP4, MOV, AVI, FLV, MPG, MPEG, WMV, 3GPP
    Max video length: ~1 hour for Flash, longer for Pro
    
    Args:
        input_path: Path to video file
        gemini_key: Gemini API key
        
    Returns:
        Description of the video content
    """
    try:
        # Configure Gemini
        genai.configure(api_key=gemini_key)
        
        # Upload video file
        logger.info(f"Uploading video file: {input_path}")
        video_file = genai.upload_file(path=input_path)
        
        # Wait for file to be processed (videos take longer)
        import time
        logger.info("Processing video... this may take a moment")
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video file processing failed: {video_file.state.name}")
        
        # Create model
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        prompt = """Generate a comprehensive description of this video that covers:
        1. The main content and subject matter
        2. Key actions or events shown
        3. Important visual details
        4. Overall context and purpose
        
        Provide a clear, detailed description suitable for fact-checking or content analysis."""
        
        response = model.generate_content([prompt, video_file])
        
        # Clean up uploaded file
        genai.delete_file(video_file.name)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error in video2text: {str(e)}")
        raise


def modal_normalization(
    modal: str = "text",
    input_data: Optional[Union[str, object]] = None,
    gemini_key: Optional[str] = None
) -> str:
    """
    Normalize different input modalities to text using Gemini API.
    
    Supported modalities:
    - "string": Direct string input
    - "text": Text file path
    - "speech": Audio file path (MP3, WAV, etc.)
    - "image": Image file path (PNG, JPEG, etc.)
    - "video": Video file path (MP4, MOV, etc.)
    
    Args:
        modal: Type of input ("string", "text", "speech", "image", "video")
        input_data: The input data (string or file path)
        gemini_key: Gemini API key (required for speech, image, video)
        
    Returns:
        Text representation of the input
        
    Raises:
        ValueError: If invalid modal type or missing API key
        NotImplementedError: If modal type not supported
    """
    logger.info(f"Processing modal: {modal}, input: {input_data}")
    
    try:
        if modal == "string":
            response = str(input_data)
            
        elif modal == "text":
            if not os.path.exists(input_data):
                raise FileNotFoundError(f"Text file not found: {input_data}")
            with open(input_data, "r", encoding="utf-8") as f:
                response = f.read()
                
        elif modal == "speech":
            if not gemini_key:
                raise ValueError("Gemini API key required for speech processing")
            if not os.path.exists(input_data):
                raise FileNotFoundError(f"Audio file not found: {input_data}")
            response = voice2text(input_data, gemini_key)
            
        elif modal == "image":
            if not gemini_key:
                raise ValueError("Gemini API key required for image processing")
            if not os.path.exists(input_data):
                raise FileNotFoundError(f"Image file not found: {input_data}")
            response = image2text(input_data, gemini_key)
            
        elif modal == "video":
            if not gemini_key:
                raise ValueError("Gemini API key required for video processing")
            if not os.path.exists(input_data):
                raise FileNotFoundError(f"Video file not found: {input_data}")
            response = video2text(input_data, gemini_key)
            
        else:
            raise NotImplementedError(f"Modal type '{modal}' is not supported")
        
        logger.info(f"Successfully processed modal: {modal}")
        return response
        
    except Exception as e:
        logger.error(f"Error in modal_normalization: {str(e)}")
        raise
