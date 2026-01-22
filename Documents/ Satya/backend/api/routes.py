from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import shutil
import os
import uuid
from models.image_detector import ImageDetector
from models.text_detector import TextDetector
from models.video_detector import VideoDetector

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

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@router.post("/analyze/image")
async def analyze_image(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(None), 
    url: str = Form(None)
):
    if not image_model:
        return {"error": "Model not loaded"}
    
    target_path_or_url = ""
    
    if url:
        target_path_or_url = url
    elif file:
        file_path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        target_path_or_url = file_path
        background_tasks.add_task(cleanup_file, file_path)
    else:
        return {"error": "No file or URL provided"}
    
    try:
        result = image_model.predict(target_path_or_url)
        return result
    except Exception as e:
        return {"error": str(e), "score": 0.5, "label": "Error"}

@router.post("/analyze/video")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not video_model:
        return {"error": "Model not loaded"}
        
    file_path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        result = video_model.process_video(file_path)
    finally:
        background_tasks.add_task(cleanup_file, file_path)
        
    return result

@router.post("/analyze/text")
async def analyze_text(text: str):
    if not text_model:
        return {"error": "Model not loaded"}
    
    result = text_model.predict(text)
    return result
