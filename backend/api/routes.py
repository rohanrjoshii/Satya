from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
import shutil
import os
import uuid
from models.image_detector import ImageDetector
from models.text_detector import TextDetector
from models.video_detector import VideoDetector
from pydantic import BaseModel
import json
import datetime
from contextlib import contextmanager

router = APIRouter()

# Initialize models (singleton pattern for simplicity)
try:
    image_model = ImageDetector()
    text_model = TextDetector()
    video_model = VideoDetector()
except Exception as e:
    print(f"Warning: Models failed to load: {e}")
    image_model = None
    text_model = None
    video_model = None

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Magic bytes for file validation
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'jpeg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',
}

@contextmanager
def temp_file(upload_dir: str, filename: str):
    """Context manager that guarantees file cleanup even on crash."""
    path = f"{upload_dir}/{uuid.uuid4()}_{filename}"
    try:
        yield path
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Warning: Failed to cleanup {path}: {e}")

def validate_image_bytes(data: bytes) -> bool:
    """Validate file is actually an image using magic bytes."""
    return any(data.startswith(magic) for magic in MAGIC_BYTES.keys())

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "models": {
            "image": image_model is not None,
            "video": video_model is not None,
            "text": text_model is not None,
        }
    }

@router.post("/analyze/image")
async def analyze_image(file: UploadFile = File(None), url: str = Form(None)):
    if not image_model:
        raise HTTPException(
            status_code=503,
            detail="Image detection model is not loaded. Check backend logs.",
        )
    
    if url:
        # URL analysis (no file cleanup needed)
        try:
            result = image_model.predict(url)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    
    elif file:
        # Validate magic bytes
        file_content = await file.read()
        if not validate_image_bytes(file_content):
            raise HTTPException(
                status_code=400, 
                detail="Invalid image file. File does not match image format signatures."
            )
        
        # Use context manager for guaranteed cleanup
        with temp_file(UPLOAD_DIR, file.filename) as file_path:
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            try:
                result = image_model.predict(file_path)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
        # File is ALWAYS deleted here, even on crash
    
    else:
        raise HTTPException(status_code=400, detail="Provide an image file or a URL.")

@router.post("/analyze/image/batch")
async def analyze_image_batch(urls: list[str] = Form(None)):
    if not image_model:
        raise HTTPException(
            status_code=503,
            detail="Image detection model is not loaded. Check backend logs.",
        )

    if not urls:
        raise HTTPException(status_code=400, detail="Provide a list of image URLs.")

    try:
        return image_model.predict_batch(urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/analyze/video")
async def analyze_video(file: UploadFile = File(...)):
    if not video_model:
        raise HTTPException(
            status_code=503,
            detail="Video detection model is not loaded. Check backend logs.",
        )
    
    # Use context manager for guaranteed cleanup
    with temp_file(UPLOAD_DIR, file.filename) as file_path:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            result = video_model.process_video(file_path)
            
            if isinstance(result, dict) and result.get("error"):
                raise HTTPException(status_code=422, detail=str(result["error"]))
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    # File is ALWAYS deleted here

@router.post("/analyze/text")
async def analyze_text(text: str):
    if not text_model:
        raise HTTPException(
            status_code=503,
            detail="Text detection model is not loaded. Check backend logs.",
        )
    
    result = text_model.predict(text)
    return result

class FeedbackModel(BaseModel):
    file_id: str | None = None
    user_verdict: str
    comments: str | None = None
    ai_score: float | None = None

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackModel):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file_id": feedback.file_id,
        "user_verdict": feedback.user_verdict,
        "comments": feedback.comments,
        "ai_score": feedback.ai_score
    }
    
    with open("feedback_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return {"status": "success", "message": "Feedback recorded"}
