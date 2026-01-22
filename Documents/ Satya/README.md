# AI Content & Deepfake Detector

A production-ready AI system to detect AI-generated images, videos, and text.

## Features
- **Multi-modal Detection**: Images (CNN + Frequency Analysis), Videos (Frame + Temporal), Text (Transformers).
- **Explainability**: Heatmaps and plain English explanations.
- **Privacy First**: No data retention.
- **Cross-Platform**: Web App + Browser Extension.

## Setup

### Backend
1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run API: `uvicorn main:app --reload`
   - API will be at `http://localhost:8000`

### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run App: `npm run dev`
   - Access at `http://localhost:5173`

### Extension
1. Open Chrome/Edge -> Extensions
2. Enable Developer Mode
3. Click "Load Unpacked" and select `extension/` folder via absolute path.

## Architecture
- **Backend**: FastAPI, PyTorch, OpenCV
- **Frontend**: React, TypeScript, TailwindCSS
- **Model**: Ensemble of EfficientNet-B4 + DCT Analysis
