import cv2
import numpy as np
import os

class VideoDetector:
    """Pure temporal analysis video detector - no ML models required."""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("Video Detector initialized (temporal analysis mode)")

    def temporal_consistency_score(self, frames):
        """
        Real faces have smooth, physically consistent motion. Deepfakes stutter.
        Measures variance in inter-frame differences.
        """
        if len(frames) < 2:
            return 0.0
        
        diffs = []
        for i in range(1, len(frames)):
            diff = np.mean(np.abs(frames[i].astype(float) - frames[i-1].astype(float)))
            diffs.append(diff)
        
        # High variance = suspicious (inconsistent motion)
        return float(np.std(diffs))

    def optical_flow_irregularity(self, frame1, frame2):
        """
        Real faces have smooth, continuous flow fields.
        Deepfake boundaries show unnatural discontinuities.
        """
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None, 
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Compute flow magnitude
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Measure discontinuities (high gradient in flow field)
        flow_grad_x = np.gradient(mag, axis=1)
        flow_grad_y = np.gradient(mag, axis=0)
        discontinuity = np.mean(np.abs(flow_grad_x) + np.abs(flow_grad_y))
        
        return float(discontinuity)

    def detect_faces_and_track(self, frames):
        """
        Track face positions across frames.
        Real video has physically plausible movement; deepfakes show impossible jumps.
        """
        face_positions = []
        
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Take largest face
                largest = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest
                center = (x + w//2, y + h//2)
                face_positions.append(center)
            else:
                face_positions.append(None)
        
        # Measure position jumps
        jumps = []
        for i in range(1, len(face_positions)):
            if face_positions[i] and face_positions[i-1]:
                dist = np.sqrt(
                    (face_positions[i][0] - face_positions[i-1][0])**2 +
                    (face_positions[i][1] - face_positions[i-1][1])**2
                )
                jumps.append(dist)
        
        if len(jumps) == 0:
            return {"avg_jump": 0, "max_jump": 0, "suspicious": False}
        
        avg_jump = np.mean(jumps)
        max_jump = np.max(jumps)
        
        # Sudden large jumps are suspicious (>100 pixels between frames)
        return {
            "avg_jump": float(avg_jump),
            "max_jump": float(max_jump),
            "suspicious": bool(max_jump > 100)
        }

    def process_video(self, video_path, frame_skip=30):
        """
        Extracts frames and runs temporal analysis.
        frame_skip: Process every Nth frame (30 = ~1 fps for 30fps video)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video file"}

        frames = []
        frame_count = 0
        
        try:
            while len(frames) < 50:  # Analyze up to 50 frames
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_skip == 0:
                    # Resize for faster processing
                    frame_resized = cv2.resize(frame, (640, 480))
                    frames.append(frame_resized)
                
                frame_count += 1
        finally:
            cap.release()

        if len(frames) < 2:
            return {"error": "Not enough frames to analyze"}

        # Run temporal analysis
        temporal_score = self.temporal_consistency_score(frames)
        
        # Optical flow on subset of frames
        flow_scores = []
        for i in range(0, len(frames)-1, 5):  # Every 5th pair
            if i+1 < len(frames):
                flow_score = self.optical_flow_irregularity(frames[i], frames[i+1])
                flow_scores.append(flow_score)
        
        avg_flow_irregularity = np.mean(flow_scores) if flow_scores else 0
        
        # Face tracking
        face_tracking = self.detect_faces_and_track(frames[::5])  # Every 5th frame
        
        # Aggregate into anomaly score
        anomaly_score = 0.0
        findings = []
        
        # Temporal consistency (threshold tuned empirically)
        if temporal_score > 15.0:
            anomaly_score += 0.3
            findings.append(f"High temporal inconsistency detected (score={temporal_score:.2f})")
        
        # Optical flow
        if avg_flow_irregularity > 2.5:
            anomaly_score += 0.3
            findings.append(f"Irregular optical flow patterns (score={avg_flow_irregularity:.2f})")
        
        # Face tracking
        if face_tracking["suspicious"]:
            anomaly_score += 0.4
            findings.append(f"Unnatural face movement detected (max jump={face_tracking['max_jump']:.1f}px)")
        
        anomaly_score = min(1.0, anomaly_score)
        
        label = "FAKE" if anomaly_score > 0.5 else "REAL"
        confidence = int(anomaly_score * 100)
        
        details = f"Analyzed {len(frames)} frames. "
        if findings:
            details += "Findings: " + "; ".join(findings)
        else:
            details += "No significant temporal anomalies detected. Motion patterns appear physically consistent."
        
        return {
            "label": label,
            "score": float(anomaly_score),
            "details": details,
            "analysis": {
                "temporal_consistency": float(temporal_score),
                "optical_flow_irregularity": float(avg_flow_irregularity),
                "face_tracking": face_tracking,
                "frames_analyzed": len(frames)
            }
        }
