from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from api.street_router import router as street_api_router
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Deepfake Detector API", version="1.0.0")

# CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(street_api_router, prefix="/api")

# Serve uploaded street-video files for MVP playback.
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/")
def read_root():
    return {
        "message": "Satya Deepfake Detector API",
        "version": "2.3.0",
        "detection_method": "Hybrid forensic + deep learning fusion model",
        "endpoints": {
            "image": "/api/analyze/image",
            "video": "/api/analyze/video", 
            "text": "/api/analyze/text",
            "feedback": "/api/feedback"
        },
        "methods": {
            "image": ["FFT Analysis", "Noise Uniformity", "Color Correlation", "ELA", "JPEG Ghost", "EXIF Metadata", "Histogram Analysis", "Edge Coherence", "Blur Consistency", "Weak Signal Aggregation"],
            "video": ["Temporal Consistency", "Optical Flow", "Face Tracking"],
            "text": ["Perplexity", "Burstiness", "Sentence Entropy", "Lexical Richness", "Punctuation"]
        }
    }
