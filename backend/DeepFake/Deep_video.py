import os
import sys
import warnings
warnings.filterwarnings('ignore')
import cv2
from moviepy import VideoFileClip
from transformers import (
        AutoImageProcessor, 
        SiglipForImageClassification,
        pipeline
    )
import torch
import librosa
import numpy as np
from PIL import Image
import torch.nn.functional as F


class CompleteDeepfakeDetector:
    """
    A comprehensive deepfake detector that analyzes both visual and audio components.
    """
    
    def __init__(
        self, 
        video_model_name="prithivMLmods/Deepfake-Detect-Siglip2",
        audio_model_name="MelodyMachine/Deepfake-audio-detection-V2",
        num_frames=20,
        frame_interval=1.0  # Extract frames every N seconds
    ):
        """
        Initialize the complete deepfake detector.
        
        Args:
            video_model_name (str): HuggingFace model for image classification
            audio_model_name (str): HuggingFace model for audio classification
            num_frames (int): Number of frames to extract from video
            frame_interval (float): Time interval (seconds) between frame extractions
        """
        self.num_frames = num_frames
        self.frame_interval = frame_interval
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        

    
        self.video_model = SiglipForImageClassification.from_pretrained(video_model_name)
        self.video_processor = AutoImageProcessor.from_pretrained(video_model_name)
        
        if torch.cuda.is_available():
            self.video_model = self.video_model.to('cuda')
        
        self.video_model.eval()
        
        # Get label mapping
        self.id2label = self.video_model.config.id2label

        try:
            self.audio_classifier = pipeline(
                "audio-classification",
                model=audio_model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            
        except Exception as e:            
            sys.exit(1)
        

    
    def extract_frames(self, video_path):
        """
        Extract frames from video at regular intervals or uniformly sampled.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            list: List of PIL Image frames
        """
 
        
        try:
            video = cv2.VideoCapture(video_path)
            
            if not video.isOpened():               
                return None
            
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            print(f"Video Info: {frame_count} frames, {fps:.2f} FPS, {duration:.2f}s duration")
            
            if frame_count == 0:
                return None
            
            # Extract frames uniformly across the video
            indices = np.linspace(0, frame_count - 1, min(self.num_frames, frame_count)).astype(int)
            
            frames = []
            timestamps = []
            
            for idx, i in enumerate(indices):
                video.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = video.read()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(frame_rgb)
                    
                    frames.append(pil_frame)
                    timestamp = i / fps if fps > 0 else idx
                    timestamps.append(timestamp)
            
            video.release()
            
            print(f"Extracted {len(frames)} frames successfully")
            return frames, timestamps
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None, None
    
    def detect_visual_deepfake(self, frames, timestamps):
        """
        Detect visual deepfakes using Siglip2 model on individual frames.
        
        Args:
            frames (list): List of PIL Image frames
            timestamps (list): Timestamps of each frame
            
        Returns:
            dict: Detection results with frame-by-frame analysis
        """
        
        try:
            frame_results = []
            fake_count = 0
            real_count = 0
            
            # Process each frame individually
            for idx, (frame, timestamp) in enumerate(zip(frames, timestamps)):
                inputs = self.video_processor(images=frame, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.to('cuda') for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.video_model(**inputs)
                
                logits = outputs.logits
                probs = F.softmax(logits, dim=1).squeeze()

                predicted_class = torch.argmax(probs).item()
                predicted_label = self.id2label[predicted_class]
                confidence = probs[predicted_class].item()
                
                frame_result = {
                    'frame_number': idx + 1,
                    'timestamp': f"{timestamp:.2f}s",
                    'prediction': predicted_label,
                    'confidence': confidence,
                    'fake_score': probs[0].item() if 0 in self.id2label else 0,
                    'real_score': probs[1].item() if 1 in self.id2label else 0
                }
                
                frame_results.append(frame_result)

                if 'fake' in predicted_label.lower():
                    fake_count += 1
                else:
                    real_count += 1

            total_frames = len(frames)
            fake_percentage = (fake_count / total_frames) * 100
            real_percentage = (real_count / total_frames) * 100

            avg_fake_score = np.mean([r['fake_score'] for r in frame_results])
            avg_real_score = np.mean([r['real_score'] for r in frame_results])
            
            overall_prediction = "FAKE" if fake_count > real_count else "REAL"
            overall_confidence = max(avg_fake_score, avg_real_score)
            
            results = {
                'frame_results': frame_results,
                'overall_prediction': overall_prediction,
                'overall_confidence': overall_confidence,
                'fake_frames': fake_count,
                'real_frames': real_count,
                'fake_percentage': fake_percentage,
                'real_percentage': real_percentage,
                'avg_fake_score': avg_fake_score,
                'avg_real_score': avg_real_score
            }
            
            print(f"Visual analysis : {fake_count} fake, {real_count} real frames")
            return results
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None
    
    def extract_audio(self, video_path, output_path="temp_audio.wav"):
        """
        Extract audio from video file.
        
        Args:
            video_path (str): Path to video file
            output_path (str): Path to save extracted audio
            
        Returns:
            str: Path to extracted audio file
        """
        
        try:
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                video.close()
                return None
            
            audio = video.audio
            audio.write_audiofile(
                output_path,
                codec='pcm_s16le',
                fps=16000,
                nbytes=2,
                buffersize=2000,
                logger=None
            )
            
            video.close()
            audio.close()
            return output_path
            
        except Exception as e:
            return None
    
    def detect_audio_deepfake(self, audio_path):
        """
        Detect audio deepfakes using Wav2Vec2 model.
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            list: Detection results with labels and scores
        """
        
        try:
            # Load audio at 16kHz
            audio_array, sr = librosa.load(audio_path, sr=16000)
            
            duration = len(audio_array) / sr
            
            # Run classification
            results = self.audio_classifier(audio_array)
            return results
            
        except Exception as e:
            return None
    
    def analyze_video(self, video_path, cleanup=True):
        """
        Complete analysis pipeline for video deepfake detection.
        
        Args:
            video_path (str): Path to video file
            cleanup (bool): Whether to delete temporary files
            
        Returns:
            dict: Complete analysis results
        """
        if not os.path.exists(video_path):
            return None

        
        results = {
            'video_path': video_path,
            'visual_detection': None,
            'audio_detection': None,
            'overall_verdict': None
        }

        
        frames_data = self.extract_frames(video_path)
        if frames_data and frames_data[0] is not None:
            frames, timestamps = frames_data
            visual_results = self.detect_visual_deepfake(frames, timestamps)
            results['visual_detection'] = visual_results

        temp_audio = "temp_extracted_audio.wav"
        audio_path = self.extract_audio(video_path, temp_audio)
        
        if audio_path:
            audio_results = self.detect_audio_deepfake(audio_path)
            results['audio_detection'] = audio_results
            
            # Cleanup
            if cleanup and os.path.exists(temp_audio):
                os.remove(temp_audio)

        
        # Generate Overall Verdict
        self._generate_verdict(results)
        
        return results
    
    def _generate_verdict(self, results):
        """
        Generate overall verdict based on visual and audio analysis.
        
        Args:
            results (dict): Analysis results
        """
        visual_deepfake = False
        audio_deepfake = False
        
        # Analyze Visual Results
        if results['visual_detection']:
            
            visual = results['visual_detection']
            
            print(f"│ Overall Prediction: {visual['overall_prediction']}")
            print(f"│ Fake Frames: {visual['fake_frames']}/{visual['fake_frames'] + visual['real_frames']} ({visual['fake_percentage']:.1f}%)")
            print(f"│ Real Frames: {visual['real_frames']}/{visual['fake_frames'] + visual['real_frames']} ({visual['real_percentage']:.1f}%)")
            print(f"│")
            print(f"│ Average Scores:")
            print(f"│   • Fake Score: {visual['avg_fake_score']*100:.2f}%")
            print(f"│   • Real Score: {visual['avg_real_score']*100:.2f}%")
            
            if visual['overall_prediction'] == 'FAKE':
                visual_deepfake = True
                verdict_text = "DEEPFAKE DETECTED"
            else:
                verdict_text = "APPEARS AUTHENTIC"
            
            print(f"│")
            print(f"│ VERDICT: {verdict_text}")
            print(f"│ Confidence: {visual['overall_confidence']*100:.2f}%")
            

        else:
            print(" Visual analysis: NOT AVAILABLE")
        
        # Analyze Audio Results
        if results['audio_detection']:
            
            for i, result in enumerate(results['audio_detection'], 1):
                label = result['label']
                score = result['score'] * 100
                print(f"│ {i}. {label.upper()}: {score:.2f}%")
            
            top_prediction = results['audio_detection'][0]
            top_label = top_prediction['label'].lower()
            
            if 'fake' in top_label:
                audio_deepfake = True
                verdict_text = "DEEPFAKE DETECTED"
            else:
                verdict_text = "APPEARS AUTHENTIC"
            
            print(f"│")
            print(f"│ VERDICT: {verdict_text}")
            print(f"│ Confidence: {top_prediction['score']*100:.2f}%")
            print("└───────────────────────────────────────────────────────────────┘")
        else:
            print("Audio analysis: NOT AVAILABLE (No audio track)")
        if visual_deepfake and audio_deepfake:
            verdict = "Both visual and audio appear to be DEEPFAKED"
            risk_level = "HIGH"
        elif visual_deepfake or audio_deepfake:
            if visual_deepfake:
                verdict = "Visual content appears DEEPFAKED"
            else:
                verdict = "Audio content appears DEEPFAKED"
            risk_level = "MEDIUM"
        else:
            verdict = "Both visual and audio appear AUTHENTIC"
            risk_level = "LOW"
        
        print(f"{verdict}")
        print(f"Risk Level: {risk_level}")
        
        results['overall_verdict'] = {
            'visual_deepfake': visual_deepfake,
            'audio_deepfake': audio_deepfake,
            'risk_level': risk_level,
            'verdict': verdict
        }



def main():

    detector = CompleteDeepfakeDetector(
        video_model_name="prithivMLmods/Deepfake-Detect-Siglip2",
        num_frames=20  # Extract 20 frames across the video
    )
    
    results = detector.analyze_video("Test_data/IMG_4707.MP4", cleanup=True)
    
    if results is None or results['overall_verdict'] is None:
        print("\n✗ Analysis failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
