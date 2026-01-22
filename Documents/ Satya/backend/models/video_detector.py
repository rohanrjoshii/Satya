import cv2
import numpy as np
import torch
from .image_detector import ImageDetector

class VideoDetector:
    def __init__(self, device='cpu'):
        self.device = device
        self.image_detector = ImageDetector(device=device)

    def process_video(self, video_path):
        """
        Analyze video frame by frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video"}
        
        frame_count = 0
        fake_frames = 0
        total_frames_analyzed = 0
        
        c = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process 1 frame every second (assuming 30fps) to save time
            if c % 30 == 0:
                # Convert to RGB and run through image detector
                # We need to save it momentarily or modify ImageDetector to accept numpy array
                # For now, let's assume we adapt ImageDetector or save temp file
                temp_path = f"temp_frame_{c}.jpg"
                cv2.imwrite(temp_path, frame)
                
                result = self.image_detector.predict(temp_path)
                if result['score'] > 0.5:
                    fake_frames += 1
                
                total_frames_analyzed += 1
                
                # Cleanup
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            c += 1
            if total_frames_analyzed > 10: # Limit for demo purposes
                break
                
        cap.release()
        
        final_score = fake_frames / total_frames_analyzed if total_frames_analyzed > 0 else 0
        return {
            "score": final_score,
            "label": "AI-Generated" if final_score > 0.5 else "Real",
            "frames_analyzed": total_frames_analyzed,
            "fake_frames_detected": fake_frames
        }
