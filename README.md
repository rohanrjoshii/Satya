# Satya: Deepfake Detection & Media Authentication Platform

A production-ready forensic analysis system to detect AI-generated images, videos, and text using **pure signal analysis** — no ML model dependencies.

## Features
- **Multi-modal Detection**: Images (FFT + Noise Analysis), Videos (Temporal + Optical Flow), Text (Statistical Heuristics)
- **Explainability**: Forensic findings in plain English with detailed metrics
- **Privacy First**: No data retention, no cloud uploads
- **Zero Model Dependencies**: Pure signal processing and statistical analysis
- **Cross-Platform**: Web App + Browser Extension

## Detection Methods

### Images
- **FFT Analysis**: Detects GAN grid patterns and diffusion model smoothness
- **Noise Uniformity**: Real cameras have consistent sensor noise; AI images don't
- **Color Channel Correlation**: Camera demosaicing creates specific R/G/B patterns
- **JPEG Ghost Analysis**: Spliced/generated regions compress differently
- **EXIF Metadata**: Checks for AI software signatures

### Videos
- **Temporal Consistency**: Measures inter-frame motion smoothness
- **Optical Flow**: Detects unnatural discontinuities in movement
- **Face Tracking**: Identifies impossible position jumps
- **Frame Analysis**: Aggregates anomalies across sampled frames

### Text
- **Perplexity Proxy**: AI text is statistically "too predictable"
- **Burstiness**: Human vocabulary is bursty; AI is uniform
- **Sentence Entropy**: AI has suspiciously consistent sentence lengths
- **Lexical Richness**: AI avoids repetition artificially (high TTR)
- **Punctuation Patterns**: AI punctuation is overly consistent

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
3. Click "Load Unpacked" and select `extension/` folder via absolute path

## Architecture
- **Backend**: FastAPI, OpenCV, NumPy (pure Python signal processing)
- **Frontend**: React, TypeScript, TailwindCSS, Framer Motion, GSAP
- **Detection**: Deterministic forensic algorithms (FFT, optical flow, statistical heuristics)

## Why No ML Models?

Traditional deepfake detectors rely on neural networks that:
- Require large downloads (GB of model weights)
- Need GPU for reasonable speed
- Are black boxes (hard to explain predictions)
- Become outdated as new generators emerge

**Satya uses forensic signal analysis** that:
- Works instantly (no model loading)
- Runs on any CPU
- Provides interpretable findings
- Is generator-agnostic (detects fundamental artifacts)

## API Endpoints

- `POST /api/analyze/image` - Analyze image file or URL
- `POST /api/analyze/video` - Analyze video file
- `POST /api/analyze/text` - Analyze text string
- `POST /api/feedback` - Submit user corrections
