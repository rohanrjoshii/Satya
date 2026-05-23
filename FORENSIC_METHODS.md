# Forensic Detection Methods

Satya uses **pure signal analysis** to detect AI-generated content. No machine learning models, no GPU required, fully interpretable results.

---

## Image Detection

### 1. FFT (Fast Fourier Transform) Analysis
**What it detects:** GAN upsampling artifacts and diffusion model smoothness

**How it works:**
- Transforms image to frequency domain
- GANs leave characteristic grid patterns from upsampling layers (checkerboard artifacts)
- Diffusion models show abnormally smooth high-frequency falloff
- Real photos have natural noise across all frequencies

**Metrics:**
- `peak_score`: Ratio of max to mean magnitude (>3.5 = suspicious)
- `hf_ratio`: High-frequency energy ratio (<0.15 = too smooth)

**Example finding:** *"FFT anomaly detected (peak=4.2, HF ratio=0.12)"*

---

### 2. Noise Uniformity Check
**What it detects:** Synthetic or absent sensor noise

**How it works:**
- Real cameras add consistent sensor noise from photon shot noise and thermal effects
- AI images have no physical sensor, so noise is either absent or artificially added
- Extracts noise residual via high-pass filter
- Measures variance across 64×64 patches
- Low variance-of-variance = suspiciously uniform

**Metrics:**
- `uniformity_score`: Variance of patch variances (<0.3 = suspicious)

**Example finding:** *"Noise pattern too uniform (score=0.23)"*

---

### 3. Color Channel Correlation
**What it detects:** Incorrect R/G/B relationships

**How it works:**
- Real cameras use Bayer filters and demosaicing algorithms
- This creates specific correlations between color channels (typically 0.85-0.98)
- AI images often have either too perfect (>0.98) or too low (<0.80) correlation
- Computes Pearson correlation between all channel pairs

**Metrics:**
- `avg_correlation`: Mean of R-G, R-B, G-B correlations
- Anomaly if outside 0.80-0.98 range

**Example finding:** *"Color channel correlation anomaly (avg=0.99)"*

---

### 4. JPEG Ghost Analysis
**What it detects:** Inconsistent compression history

**How it works:**
- Re-compresses image at quality 95
- Computes pixel-wise difference from original
- Spliced or generated regions compress differently than authentic regions
- High ghost score indicates inconsistent compression (multiple edits or generation)

**Metrics:**
- `ghost_score`: Mean absolute difference (>8.0 = suspicious)

**Example finding:** *"JPEG ghost detected (score=9.3)"*

---

### 5. EXIF Metadata Analysis
**What it detects:** AI software signatures

**How it works:**
- Parses EXIF metadata from image file
- Checks for known AI generator signatures (Stable Diffusion, Midjourney, DALL-E, etc.)
- Missing EXIF is also suspicious (common in AI images)

**Example finding:** *"Generative AI signature found: Stable Diffusion"*

---

## Video Detection

### 1. Temporal Consistency Score
**What it detects:** Unnatural motion patterns

**How it works:**
- Real faces have smooth, physically consistent motion
- Deepfakes often "stutter" between frames due to per-frame generation
- Computes mean pixel difference between consecutive frames
- Measures variance of these differences
- High variance = inconsistent motion = suspicious

**Metrics:**
- `temporal_consistency`: Standard deviation of inter-frame diffs (>15.0 = suspicious)

**Example finding:** *"High temporal inconsistency detected (score=18.4)"*

---

### 2. Optical Flow Irregularity
**What it detects:** Unnatural discontinuities in movement

**How it works:**
- Uses Farneback optical flow algorithm to compute motion vectors
- Real faces have smooth, continuous flow fields
- Deepfake boundaries (especially hairline/jaw) show unnatural discontinuities
- Measures gradient of flow magnitude (discontinuity score)

**Metrics:**
- `optical_flow_irregularity`: Mean flow gradient (>2.5 = suspicious)

**Example finding:** *"Irregular optical flow patterns (score=3.1)"*

---

### 3. Face Tracking
**What it detects:** Impossible position jumps

**How it works:**
- Uses Haar Cascade to detect faces in each frame
- Tracks face center position across frames
- Real video has physically plausible movement
- Deepfakes often show impossible snap rotations or position jumps

**Metrics:**
- `max_jump`: Maximum pixel distance between frames (>100px = suspicious)

**Example finding:** *"Unnatural face movement detected (max jump=142px)"*

---

## Text Detection

### 1. Perplexity Proxy (Character Entropy)
**What it detects:** Statistically "too predictable" text

**How it works:**
- AI text picks high-probability words, making it statistically predictable
- Computes character-level entropy as proxy for perplexity
- English text typically has ~4.5 bits/char entropy
- AI text tends to be slightly lower (~4.0-4.3)

**Metrics:**
- `entropy`: Character-level entropy (<4.0 = suspicious)

**Example finding:** *"Low entropy detected (too predictable, entropy=3.8)"*

---

### 2. Burstiness
**What it detects:** Uniform vocabulary distribution

**How it works:**
- Human writing has "bursty" vocabulary: use a word rarely, then cluster it
- AI writing uses vocabulary more uniformly (avoids repetition artificially)
- Measures coefficient of variation of word frequencies
- Human text: burstiness > 2.0
- AI text: burstiness < 1.5

**Metrics:**
- `burstiness`: CV of word frequencies (<1.5 = suspicious)

**Example finding:** *"Uniform vocabulary distribution (burstiness=1.2)"*

---

### 3. Sentence Length Entropy
**What it detects:** Suspiciously uniform sentence lengths

**How it works:**
- AI tends toward uniform sentence lengths
- Humans vary wildly (short punchy sentences, then long rambling ones)
- Bins sentence lengths into groups of 5 words
- Computes entropy over distribution
- Low entropy = suspiciously uniform

**Metrics:**
- `entropy`: Sentence length distribution entropy (<1.5 = suspicious)

**Example finding:** *"Suspiciously uniform sentence lengths (entropy=1.3)"*

---

### 4. Lexical Richness (Type-Token Ratio)
**What it detects:** Artificially high vocabulary diversity

**How it works:**
- AI writing in long texts has higher TTR than humans
- AI avoids repetition artificially to seem more "creative"
- Measures unique words / total words in sliding 50-word windows
- Human text: TTR 0.5-0.7
- AI text: TTR > 0.75

**Metrics:**
- `ttr`: Type-token ratio (>0.75 = suspicious)

**Example finding:** *"Artificially high lexical diversity (TTR=0.82)"*

---

### 5. Punctuation Patterns
**What it detects:** Overly consistent punctuation usage

**How it works:**
- AI text has suspiciously consistent punctuation usage
- Humans are more erratic (sometimes comma-heavy, sometimes sparse)
- Counts commas per sentence
- Measures variance across sentences
- Low variance = suspiciously consistent

**Metrics:**
- `variance`: Variance of comma counts (<0.5 = suspicious)

**Example finding:** *"Overly consistent punctuation patterns (variance=0.3)"*

---

## Scoring System

Each detector returns a score from 0.0 to 1.0:
- **0.0-0.3**: Likely authentic/human
- **0.3-0.5**: Uncertain/mixed signals
- **0.5-0.8**: Suspicious/likely AI
- **0.8-1.0**: High confidence AI-generated

Scores are aggregated from multiple forensic tests, each weighted by reliability.

---

## Advantages Over ML Models

| Aspect | ML Models | Signal Analysis |
|--------|-----------|-----------------|
| **Speed** | Slow (GPU required) | Instant (pure CPU) |
| **Size** | GB of weights | KB of code |
| **Interpretability** | Black box | Every finding explained |
| **Robustness** | Outdated by new generators | Generator-agnostic |
| **Privacy** | May phone home | 100% local |
| **Dependencies** | PyTorch, CUDA, etc. | NumPy, OpenCV |

---

## Limitations

- **Image**: May flag heavily compressed real photos as suspicious
- **Video**: Requires faces for tracking (doesn't work on landscapes)
- **Text**: Short texts (<50 words) are hard to analyze reliably
- **All**: Adversarial attacks can fool forensic methods (but also fool ML models)

---

## References

- **FFT Analysis**: Marra et al., "Do GANs Leave Specific Traces?" (2019)
- **Noise Analysis**: Cozzolino et al., "Noiseprint" (2019)
- **Optical Flow**: Amerini et al., "Deepfake Video Detection" (2019)
- **Text Statistics**: Gehrmann et al., "GLTR: Statistical Detection" (2019)
