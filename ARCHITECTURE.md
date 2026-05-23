# Satya Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  React + TypeScript + TailwindCSS + Framer Motion + GSAP   │
│                                                              │
│  Pages:                                                      │
│  • Home (Hero, Features, How It Works)                      │
│  • Analysis (Upload, URL input, Results)                    │
│                                                              │
│  Components:                                                 │
│  • FileUpload (Drag-drop, URL input)                        │
│  • ResultsDashboard (Scores, charts, findings)              │
│  • FlipTextReveal (GSAP animation)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/REST
                   │ (Axios)
┌──────────────────▼──────────────────────────────────────────┐
│                      Backend API                             │
│                   FastAPI + Python                           │
│                                                              │
│  Endpoints:                                                  │
│  • POST /api/analyze/image                                  │
│  • POST /api/analyze/video                                  │
│  • POST /api/analyze/text                                   │
│  • POST /api/feedback                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────┐
        │                     │              │
┌───────▼────────┐  ┌────────▼────────┐  ┌─▼──────────────┐
│ ImageDetector  │  │ VideoDetector   │  │ TextDetector   │
│                │  │                 │  │                │
│ • FFT Analysis │  │ • Temporal      │  │ • Perplexity   │
│ • Noise Check  │  │   Consistency   │  │ • Burstiness   │
│ • Color Corr.  │  │ • Optical Flow  │  │ • Sentence     │
│ • JPEG Ghost   │  │ • Face Tracking │  │   Entropy      │
│ • EXIF Meta    │  │                 │  │ • Lexical      │
│                │  │                 │  │   Richness     │
└────────┬───────┘  └────────┬────────┘  └─┬──────────────┘
         │                   │              │
         └───────────┬───────┴──────────────┘
                     │
         ┌───────────▼────────────┐
         │   RealityChecker       │
         │   (Forensic Engine)    │
         │                        │
         │ • FFT Anomaly Score    │
         │ • Noise Uniformity     │
         │ • Color Correlation    │
         │ • JPEG Ghost Analysis  │
         │ • Metadata Extraction  │
         └────────────────────────┘
```

---

## Detection Pipeline

### Image Analysis Flow

```
Image Input (File/URL)
    │
    ├─► Load & Convert to RGB
    │
    ├─► RealityChecker.perform_full_check()
    │   │
    │   ├─► FFT Analysis
    │   │   └─► Detect GAN grid patterns
    │   │       Measure high-frequency energy
    │   │
    │   ├─► Noise Uniformity
    │   │   └─► Extract noise residual
    │   │       Measure patch variance
    │   │
    │   ├─► Color Correlation
    │   │   └─► Compute R/G/B correlations
    │   │       Check for anomalies
    │   │
    │   ├─► JPEG Ghost
    │   │   └─► Re-compress at Q95
    │   │       Measure difference
    │   │
    │   └─► EXIF Metadata
    │       └─► Parse metadata
    │           Check for AI signatures
    │
    └─► Aggregate Scores
        │
        ├─► Reality Score (0.0-1.0)
        ├─► AI Likelihood (1.0 - reality_score)
        ├─► Findings List
        └─► Detailed Metrics
```

### Video Analysis Flow

```
Video Input (File)
    │
    ├─► Extract Frames (every 30th)
    │
    ├─► Temporal Consistency
    │   └─► Compute inter-frame diffs
    │       Measure variance
    │
    ├─► Optical Flow (every 5th pair)
    │   └─► Farneback algorithm
    │       Measure discontinuities
    │
    ├─► Face Tracking
    │   └─► Haar Cascade detection
    │       Track position jumps
    │
    └─► Aggregate Anomaly Score
        │
        ├─► Temporal Score
        ├─► Flow Irregularity
        ├─► Face Jump Detection
        └─► Findings List
```

### Text Analysis Flow

```
Text Input (String)
    │
    ├─► Perplexity Proxy
    │   └─► Character-level entropy
    │       Check if too predictable
    │
    ├─► Burstiness
    │   └─► Word frequency distribution
    │       Measure coefficient of variation
    │
    ├─► Sentence Entropy
    │   └─► Sentence length distribution
    │       Check uniformity
    │
    ├─► Lexical Richness
    │   └─► Type-Token Ratio
    │       Sliding window analysis
    │
    ├─► Punctuation Patterns
    │   └─► Comma variance
    │       Check consistency
    │
    └─► Aggregate AI Score
        │
        ├─► Statistical Metrics
        ├─► Findings List
        └─► Detailed Analysis
```

---

## File Structure

```
satya/
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── requirements.txt           # Python dependencies (50MB)
│   │
│   ├── api/
│   │   ├── routes.py              # API endpoints
│   │   ├── preprocessing.py       # Input validation
│   │   └── postprocessing.py      # Response formatting
│   │
│   ├── models/
│   │   ├── image_detector.py      # Image forensics
│   │   ├── video_detector.py      # Video temporal analysis
│   │   └── text_detector.py       # Text statistics
│   │
│   ├── utils/
│   │   ├── reality_checker.py     # Core forensic engine
│   │   └── evaluation.py          # Metrics & benchmarks
│   │
│   ├── uploads/                   # Temporary file storage
│   └── feedback_log.jsonl         # User feedback log
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx           # Landing page
│   │   │   └── Analysis.tsx       # Analysis interface
│   │   │
│   │   ├── components/
│   │   │   ├── FileUpload.tsx     # Upload component
│   │   │   ├── ResultsDashboard.tsx # Results display
│   │   │   ├── Navbar.tsx         # Navigation
│   │   │   └── pixel-perfect/
│   │   │       ├── flip-text-reveal.tsx  # GSAP animation
│   │   │       └── stagger1.tsx          # Grid animation
│   │   │
│   │   └── main.tsx               # React entry point
│   │
│   ├── package.json               # Node dependencies
│   └── vite.config.ts             # Build config
│
├── extension/
│   ├── manifest.json              # Chrome extension config
│   ├── background.js              # Service worker
│   ├── content.js                 # Page injection
│   └── popup/
│       ├── popup.html             # Extension UI
│       └── popup.js               # Extension logic
│
├── README.md                      # Quick start guide
├── FORENSIC_METHODS.md            # Detection algorithms
├── MIGRATION_GUIDE.md             # v1 → v2 upgrade
├── ARCHITECTURE.md                # This file
└── docker-compose.yml             # Container orchestration
```

---

## Data Flow

### Image Upload Example

```
1. User drags image into FileUpload component
   └─► FileUpload.tsx validates file type

2. FileUpload calls handleFileSelect()
   └─► Analysis.tsx creates FormData

3. Axios POST to /api/analyze/image
   └─► routes.py receives file

4. routes.py saves to /uploads/
   └─► Calls image_detector.predict()

5. ImageDetector loads image
   └─► Calls reality_checker.perform_full_check()

6. RealityChecker runs 5 forensic tests
   └─► Returns reality_score + findings

7. ImageDetector aggregates results
   └─► Converts to AI likelihood
   └─► Generates explanation

8. routes.py returns JSON response
   └─► Deletes uploaded file (background task)

9. Analysis.tsx receives response
   └─► Updates state to 'success'
   └─► Renders ResultsDashboard

10. ResultsDashboard displays:
    ├─► Score gauge
    ├─► Findings list
    ├─► Detailed metrics
    └─► Forensic breakdown
```

---

## Technology Choices

### Why FastAPI?
- Async support for concurrent requests
- Automatic OpenAPI docs
- Type hints for validation
- Fast (comparable to Node.js)

### Why OpenCV + NumPy?
- Battle-tested computer vision library
- Pure C++ backend (fast)
- No GPU required
- Extensive documentation

### Why React + TypeScript?
- Type safety prevents runtime errors
- Component reusability
- Large ecosystem (shadcn/ui)
- Vite for fast builds

### Why No ML Models?
- **Interpretability**: Every finding is explainable
- **Speed**: No model loading overhead
- **Size**: 98% smaller than ML approach
- **Robustness**: Generator-agnostic detection
- **Privacy**: 100% local, no external calls

---

## Performance Characteristics

### Bottlenecks

1. **Image FFT**: O(n log n) where n = pixels
   - 512×512: ~10ms
   - 2048×2048: ~100ms

2. **Video Optical Flow**: O(frames × pixels)
   - 30s video @ 30fps: ~5-10s
   - Mitigated by frame skipping

3. **Text Statistics**: O(words²) for burstiness
   - 500 words: ~50ms
   - 5000 words: ~500ms

### Optimizations

- Frame skipping (analyze every 30th frame)
- Image resizing (640×480 for video frames)
- Sliding window analysis (text)
- Background file cleanup (async)

---

## Security Considerations

### Input Validation
- File size limits (10MB images, 100MB videos)
- MIME type checking
- Path traversal prevention
- URL validation (no file://, no localhost)

### Privacy
- No data retention (files deleted after analysis)
- No external API calls
- No telemetry or tracking
- Optional feedback logging (user-controlled)

### Rate Limiting
- Not implemented (add nginx rate limiting in production)
- Recommend: 10 requests/minute per IP

---

## Deployment Options

### Local Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Docker
```bash
docker-compose up --build
# Frontend: http://localhost:80
# Backend: http://localhost:8000
```

### Production (Recommended)
```
┌─────────────┐
│   Nginx     │  (Reverse proxy, SSL, rate limiting)
│   :443      │
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
┌──▼──┐  ┌─▼────┐
│React│  │FastAPI│
│:3000│  │:8000  │
└─────┘  └───────┘
```

---

## Future Architecture

### Planned Additions

1. **WebAssembly Port**
   - Run forensics in browser
   - No backend needed for basic analysis

2. **Blockchain Verification**
   - Store content hashes on-chain
   - Provenance tracking

3. **Audio Deepfake Detection**
   - Spectrogram analysis
   - Voice consistency checks

4. **Batch Processing API**
   - Analyze multiple files
   - Async job queue (Celery)

5. **Real-time Video Stream**
   - WebRTC integration
   - Live deepfake detection
