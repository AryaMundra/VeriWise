# backend/utils/multimodal.py
import cv2
import numpy as np
from moviepy import VideoFileClip

def extract_frames(video_path, max_frames=6):
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            times = np.linspace(0, duration, min(max_frames, 6)+2)[1:-1]
            for t in times:
                frame = clip.get_frame(t)
                frames.append(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            clip.reader.close()
            return frames
        idxs = np.linspace(0, total-1, min(max_frames, total)).astype(int)
        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        cap.release()
    except Exception as e:
        print("Frame extraction error:", e)
    return frames

def extract_audio_text(video_path):
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.reader.close()
        transcript = "AUTO_TRANSCRIPT_PLACEHOLDER"
        return {"duration": duration, "transcript": transcript}
    except Exception as e:
        print("Audio/text extraction error:", e)
        return {"duration": None, "transcript": ""}

def multimodal_extract(video_path=None, text_input=None):
    frames, transcript = [], ""
    if video_path:
        frames = extract_frames(video_path)
        transcript = extract_audio_text(video_path).get("transcript", "")
    return {"frames": frames, "transcript": transcript, "text_input": text_input or ""}