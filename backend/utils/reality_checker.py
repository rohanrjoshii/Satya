import numpy as np
import cv2
from PIL import Image
from PIL.ExifTags import TAGS
from collections import Counter
import math

# Weights for forensic tests (must sum to 1.0)
FORENSIC_WEIGHTS = {
    "fft": 0.18,           # GAN/diffusion fingerprints
    "noise": 0.16,         # Sensor noise patterns
    "color": 0.10,         # Camera demosaicing
    "ela": 0.16,           # Error level analysis
    "jpeg": 0.07,          # JPEG ghost
    "metadata": 0.07,      # AI software signatures
    "histogram": 0.10,     # Histogram anomalies (NEW)
    "edge_coherence": 0.08,# Edge pattern analysis (NEW)
    "blur_consistency": 0.08 # Depth-of-field analysis (NEW)
}

FORENSIC_FEATURE_NAMES = [
    "fft_peak_score",
    "fft_grid_score",
    "fft_hf_ratio",
    "noise_uniformity_score",
    "noise_avg_level",
    "color_avg_correlation",
    "ela_score",
    "ela_bright_pixel_ratio",
    "jpeg_ghost_score",
    "metadata_ai_flag",
    "histogram_smoothness",
    "histogram_clip_low",
    "histogram_clip_high",
    "edge_density",
    "edge_uniformity",
    "blur_uniformity",
    "blur_range",
]

# AI software signatures to detect
AI_SOFTWARE_SIGNATURES = [
    'stable diffusion', 'midjourney', 'dall-e', 'dall·e',
    'firefly', 'runway', 'invoke ai', 'comfyui', 'automatic1111',
    'novelai', 'craiyon', 'imagen', 'parti'
]

class RealityChecker:
    """Pure signal analysis for deepfake detection - no ML models required."""
    
    def __init__(self, device='cpu'):
        self.device = device
        print("Reality Checker initialized (pure signal analysis mode)")

    def fft_anomaly_score(self, img_gray):
        """
        Detects GAN/diffusion fingerprints in frequency domain.
        Improved with tighter thresholds for modern AI generators.
        """
        f = np.fft.fft2(img_gray)
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        
        center = np.array(magnitude.shape) // 2
        
        # Mask DC component (center)
        magnitude[center[0]-10:center[0]+10, center[1]-10:center[1]+10] = 0
        
        # Normalize peak relative to LOCAL neighborhood
        peak_val = magnitude.max()
        local_region = magnitude[
            max(0, center[0]-50):min(magnitude.shape[0], center[0]+50),
            max(0, center[1]-50):min(magnitude.shape[1], center[1]+50)
        ]
        local_mean = local_region.mean()
        peak_score = peak_val / (local_mean + 1e-6)
        
        # Check for periodic grid pattern (GAN/diffusion upsampling artifact)
        rows = np.mean(magnitude, axis=1)
        cols = np.mean(magnitude, axis=0)
        row_fft = np.abs(np.fft.fft(rows))
        col_fft = np.abs(np.fft.fft(cols))
        
        # Grid score: periodic peaks in 1D FFT of row/col means
        grid_score_row = row_fft[1:len(row_fft)//2].max() / (row_fft[1:len(row_fft)//2].mean() + 1e-6)
        grid_score_col = col_fft[1:len(col_fft)//2].max() / (col_fft[1:len(col_fft)//2].mean() + 1e-6)
        grid_score = (grid_score_row + grid_score_col) / 2
        
        # High-frequency energy ratio (AI images often have unnatural HF distribution)
        h, w = magnitude.shape
        high_freq_mask = np.zeros_like(magnitude)
        high_freq_mask[0:h//4, :] = 1
        high_freq_mask[3*h//4:, :] = 1
        high_freq_mask[:, 0:w//4] = 1
        high_freq_mask[:, 3*w//4:] = 1
        
        high_freq_energy = np.sum(magnitude * high_freq_mask)
        total_energy = np.sum(magnitude)
        hf_ratio = high_freq_energy / (total_energy + 1e-6)
        
        # ULTRA-AGGRESSIVE THRESHOLDS: Use OR logic with multiple indicators
        # Modern AI generators trigger at least one of these
        anomaly = bool(
            peak_score > 2.2 or           # Very aggressive (was 2.8)
            grid_score > 1.5 or           # Very aggressive (was 2.0)
            hf_ratio < 0.20 or            # Wider range (was 0.18)
            hf_ratio > 0.38 or            # Tighter (was 0.40)
            (peak_score > 1.8 and grid_score > 1.2)  # Combined weak signals
        )
        
        return {
            "peak_score": float(peak_score),
            "grid_score": float(grid_score),
            "hf_ratio": float(hf_ratio),
            "anomaly": anomaly
        }

    def noise_uniformity_check(self, img):
        """
        Real cameras add consistent sensor noise. AI images have synthetic/absent noise.
        Measures noise variance across patches - AI is suspiciously uniform.
        IMPROVED: More sensitive to AI-generated smoothness.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Extract noise residual (high-pass filter)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = cv2.subtract(gray, blurred)
        
        # Split into patches and measure variance
        h, w = noise.shape
        patch_size = 64
        variances = []
        
        for i in range(0, h - patch_size, patch_size):
            for j in range(0, w - patch_size, patch_size):
                patch = noise[i:i+patch_size, j:j+patch_size]
                variances.append(np.var(patch))
        
        if len(variances) == 0:
            return {"uniformity_score": 0.5, "suspicious": False}
        
        # Low variance of variances = suspiciously uniform noise
        variance_of_variance = np.var(variances)
        mean_variance = np.mean(variances)
        uniformity_score = variance_of_variance / (mean_variance + 1e-6)
        
        # Also check absolute noise level (AI images often too clean)
        avg_noise_level = np.mean(np.abs(noise))
        
        # ULTRA-AGGRESSIVE: Flag if too uniform OR too clean OR too perfect
        suspicious = bool(
            uniformity_score < 0.6 or      # Very aggressive (was 0.5)
            avg_noise_level < 3.5 or       # Raised (was 3.0)
            (uniformity_score < 0.8 and avg_noise_level < 4.0)  # Combined signals
        )
        
        return {
            "uniformity_score": float(uniformity_score),
            "avg_noise_level": float(avg_noise_level),
            "suspicious": suspicious
        }

    def color_channel_correlation(self, img):
        """
        Real photos have specific R/G/B correlations from camera demosaicing.
        AI images often have subtly wrong inter-channel statistics.
        """
        if len(img.shape) != 3:
            return {"correlation_anomaly": False, "message": "Grayscale image"}
        
        b, g, r = cv2.split(img)
        
        # Flatten and compute correlations
        b_flat = b.flatten().astype(float)
        g_flat = g.flatten().astype(float)
        r_flat = r.flatten().astype(float)
        
        corr_rg = np.corrcoef(r_flat, g_flat)[0, 1]
        corr_rb = np.corrcoef(r_flat, b_flat)[0, 1]
        corr_gb = np.corrcoef(g_flat, b_flat)[0, 1]
        
        # Real photos typically have 0.85-0.96 correlation between channels
        # AI images often show either too perfect (>0.96) or unusual (<0.84) correlation
        avg_corr = (corr_rg + corr_rb + corr_gb) / 3
        anomaly = bool(avg_corr > 0.96 or avg_corr < 0.84)  # Ultra-tight range
        
        return {
            "avg_correlation": float(avg_corr),
            "rg": float(corr_rg),
            "rb": float(corr_rb),
            "gb": float(corr_gb),
            "anomaly": anomaly
        }

    def ela_analysis(self, img, image_path):
        """
        Error Level Analysis - detects copy-paste forgeries and AI generation.
        Analyzes JPEG compression inconsistencies across the image.
        IMPROVED: More sensitive thresholds for AI detection.
        """
        # Skip for non-JPEG formats
        if not image_path.lower().endswith(('.jpg', '.jpeg')):
            return {
                "ela_score": 0.0,
                "suspicious": False,
                "skipped": True,
                "reason": "Not a JPEG file"
            }
        
        # Re-save at quality 90
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, encoded = cv2.imencode('.jpg', img, encode_param)
        recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        
        # Compute absolute difference
        diff = cv2.absdiff(img, recompressed)
        
        # Convert to grayscale for analysis
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Analyze variance across regions
        h, w = diff_gray.shape
        block_size = 64
        variances = []
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = diff_gray[i:i+block_size, j:j+block_size]
                variances.append(np.var(block))
        
        if len(variances) == 0:
            return {"ela_score": 0.0, "suspicious": False, "skipped": True}
        
        # High variance of variances = inconsistent compression = suspicious
        variance_of_variance = np.var(variances)
        mean_variance = np.mean(variances)
        ela_score = variance_of_variance / (mean_variance + 1e-6)
        
        # Also check for extreme bright spots (common in AI images)
        bright_pixels = np.sum(diff_gray > 50) / diff_gray.size
        
        # ULTRA-AGGRESSIVE THRESHOLDS
        suspicious = bool(ela_score > 8.0 or bright_pixels > 0.08)  # Very aggressive (was 10.0 and 0.10)
        
        return {
            "ela_score": float(ela_score),
            "bright_pixel_ratio": float(bright_pixels),
            "suspicious": suspicious,
            "skipped": False
        }

    def histogram_anomaly_check(self, img):
        """
        NEW: Analyzes color histogram distribution.
        AI images often have unnatural histogram patterns (too smooth, clipped, or bimodal).
        """
        if len(img.shape) != 3:
            return {"histogram_anomaly": False, "message": "Grayscale image"}
        
        # Calculate histogram for each channel
        hist_b = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
        hist_g = cv2.calcHist([img], [1], None, [256], [0, 256]).flatten()
        hist_r = cv2.calcHist([img], [2], None, [256], [0, 256]).flatten()
        
        # Normalize
        hist_b = hist_b / (hist_b.sum() + 1e-6)
        hist_g = hist_g / (hist_g.sum() + 1e-6)
        hist_r = hist_r / (hist_r.sum() + 1e-6)
        
        # Check for clipping (AI often clips at 0 or 255)
        clip_low = (hist_b[0] + hist_g[0] + hist_r[0]) / 3
        clip_high = (hist_b[255] + hist_g[255] + hist_r[255]) / 3
        
        # Check for smoothness (AI histograms are often too smooth)
        def histogram_smoothness(hist):
            # Calculate second derivative (measure of roughness)
            diff2 = np.diff(np.diff(hist))
            return np.mean(np.abs(diff2))
        
        smoothness_b = histogram_smoothness(hist_b)
        smoothness_g = histogram_smoothness(hist_g)
        smoothness_r = histogram_smoothness(hist_r)
        avg_smoothness = (smoothness_b + smoothness_g + smoothness_r) / 3
        
        # Real photos have rougher histograms (more variation)
        # AI images are suspiciously smooth OR have clipping
        anomaly = bool(
            avg_smoothness < 0.00005 or    # Much more lenient (was 0.00002)
            clip_low > 0.02 or             # More aggressive (was 0.03)
            clip_high > 0.02 or            # More aggressive (was 0.03)
            (avg_smoothness < 0.0001 and (clip_low > 0.01 or clip_high > 0.01))  # Combined
        )
        
        return {
            "avg_smoothness": float(avg_smoothness),
            "clip_low": float(clip_low),
            "clip_high": float(clip_high),
            "anomaly": anomaly
        }

    def edge_coherence_check(self, img):
        """
        NEW: Analyzes edge patterns and coherence.
        AI images often have edges that are too perfect or have unnatural sharpness transitions.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Detect edges using Canny
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        # Calculate edge strength variation
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Split into patches and measure edge strength variance
        h, w = edge_magnitude.shape
        patch_size = 64
        edge_strengths = []
        
        for i in range(0, h - patch_size, patch_size):
            for j in range(0, w - patch_size, patch_size):
                patch = edge_magnitude[i:i+patch_size, j:j+patch_size]
                edge_strengths.append(np.mean(patch))
        
        if len(edge_strengths) == 0:
            return {"edge_anomaly": False, "edge_density": 0.0}
        
        edge_variance = np.var(edge_strengths)
        mean_edge_strength = np.mean(edge_strengths)
        edge_uniformity = edge_variance / (mean_edge_strength + 1e-6)
        
        # AI images often have:
        # 1. Too uniform edge distribution (low variance)
        # 2. Unnatural edge density (too high or too low)
        anomaly = bool(
            edge_uniformity < 0.5 or       # Very aggressive (was 0.4)
            edge_density < 0.04 or         # Raised (was 0.03)
            edge_density > 0.20 or         # Lowered (was 0.22)
            (edge_uniformity < 0.7 and edge_density < 0.06)  # Combined weak signals
        )
        
        return {
            "edge_density": float(edge_density),
            "edge_uniformity": float(edge_uniformity),
            "mean_edge_strength": float(mean_edge_strength),
            "anomaly": anomaly
        }

    def blur_consistency_check(self, img):
        """
        NEW: Analyzes depth-of-field and blur consistency.
        AI images often have synthetic bokeh or inconsistent blur patterns.
        Real cameras have physically accurate depth-of-field.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Calculate local blur using Laplacian variance
        h, w = gray.shape
        patch_size = 64
        blur_scores = []
        
        for i in range(0, h - patch_size, patch_size):
            for j in range(0, w - patch_size, patch_size):
                patch = gray[i:i+patch_size, j:j+patch_size]
                laplacian = cv2.Laplacian(patch, cv2.CV_64F)
                blur_score = np.var(laplacian)
                blur_scores.append(blur_score)
        
        if len(blur_scores) == 0:
            return {"blur_anomaly": False, "blur_variance": 0.0}
        
        # Analyze blur distribution
        blur_variance = np.var(blur_scores)
        mean_blur = np.mean(blur_scores)
        blur_uniformity = blur_variance / (mean_blur + 1e-6)
        
        # Check for unnatural blur transitions
        # AI often creates either too uniform blur OR unrealistic bokeh
        blur_scores_sorted = sorted(blur_scores)
        q1 = blur_scores_sorted[len(blur_scores_sorted)//4]
        q3 = blur_scores_sorted[3*len(blur_scores_sorted)//4]
        blur_range = q3 - q1
        
        # AI images often have:
        # 1. Suspiciously uniform blur (all sharp or all blurry)
        # 2. Unnatural blur transitions (too abrupt)
        # 3. Synthetic bokeh patterns
        anomaly = bool(
            blur_uniformity < 0.20 or      # Very aggressive (was 0.15)
            blur_range < 80 or             # Raised (was 50)
            (mean_blur < 150 and blur_uniformity < 0.4) or  # Adjusted (was 100/0.3)
            (blur_uniformity < 0.3 and blur_range < 120)  # Combined signals
        )
        
        return {
            "blur_variance": float(blur_variance),
            "blur_uniformity": float(blur_uniformity),
            "mean_blur": float(mean_blur),
            "blur_range": float(blur_range),
            "anomaly": anomaly
        }

    def jpeg_ghost_analysis(self, img, image_path):
        """
        Re-compress at multiple quality levels and diff against original.
        Spliced/generated regions compress differently, leaving "ghosts".
        Only applies to JPEG files.
        """
        # Skip for non-JPEG formats
        if not image_path.lower().endswith(('.jpg', '.jpeg')):
            return {
                "ghost_score": 0.0,
                "suspicious": False,
                "skipped": True,
                "reason": "Not a JPEG file"
            }
        
        # Encode at quality 95
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        _, encoded = cv2.imencode('.jpg', img, encode_param)
        recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        
        # Compute difference
        diff = cv2.absdiff(img, recompressed)
        ghost_score = np.mean(diff)
        
        # High ghost score indicates inconsistent compression (suspicious)
        return {
            "ghost_score": float(ghost_score),
            "suspicious": bool(ghost_score > 8.0),
            "skipped": False
        }

    def check_metadata(self, image_path):
        """
        Analyzes EXIF data for AI generation signatures.
        Only flags if AI software is positively identified.
        Absence of EXIF = inconclusive, not suspicious.
        """
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if not exif_data:
                return {
                    "status": "inconclusive", 
                    "message": "No EXIF metadata (common in screenshots, social media)",
                    "ai_detected": False
                }
            
            metadata = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                metadata[tag] = str(value)
            
            # Check for AI-related software signatures
            software = str(metadata.get('Software', '')).lower()
            user_comment = str(metadata.get('UserComment', '')).lower()
            image_description = str(metadata.get('ImageDescription', '')).lower()
            
            all_text = f"{software} {user_comment} {image_description}"
            
            for signature in AI_SOFTWARE_SIGNATURES:
                if signature in all_text:
                    return {
                        "status": "danger", 
                        "message": f"AI generator detected: {signature}",
                        "ai_detected": True
                    }
            
            return {
                "status": "success", 
                "message": "Metadata appears consistent with standard capture.",
                "ai_detected": False
            }
            
        except Exception as e:
            return {
                "status": "inconclusive", 
                "message": "Could not read EXIF data",
                "ai_detected": False
            }

    def _run_all_checks(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        return {
            "fft": self.fft_anomaly_score(gray),
            "noise": self.noise_uniformity_check(img),
            "color": self.color_channel_correlation(img),
            "ela": self.ela_analysis(img, image_path),
            "jpeg": self.jpeg_ghost_analysis(img, image_path),
            "metadata": self.check_metadata(image_path),
            "histogram": self.histogram_anomaly_check(img),
            "edge": self.edge_coherence_check(img),
            "blur": self.blur_consistency_check(img),
        }

    def get_forensic_feature_vector(self, image_path):
        results = self._run_all_checks(image_path)
        if results is None:
            return None

        vector = np.array([
            results["fft"]["peak_score"] / 10.0,
            results["fft"]["grid_score"] / 10.0,
            results["fft"]["hf_ratio"],
            results["noise"]["uniformity_score"] / 2.0,
            min(results["noise"]["avg_noise_level"] / 20.0, 1.0),
            results["color"]["avg_correlation"],
            min(results["ela"]["ela_score"] / 20.0, 1.0),
            results["ela"]["bright_pixel_ratio"],
            min(results["jpeg"]["ghost_score"] / 50.0, 1.0),
            1.0 if results["metadata"].get("ai_detected") else 0.0,
            min(results["histogram"]["avg_smoothness"] / 0.0005, 1.0),
            results["histogram"]["clip_low"],
            results["histogram"]["clip_high"],
            min(results["edge"]["edge_density"] / 0.25, 1.0),
            min(results["edge"]["edge_uniformity"] / 2.0, 1.0),
            min(results["blur"]["blur_uniformity"] / 1.0, 1.0),
            min(results["blur"]["blur_range"] / 255.0, 1.0),
        ], dtype=np.float32)

        return {
            "vector": vector,
            "feature_names": FORENSIC_FEATURE_NAMES,
            "results": results,
        }

    def perform_full_check(self, image_path):
        """Runs all forensic checks and aggregates results with weighted scoring."""
        try:
            feature_payload = self.get_forensic_feature_vector(image_path)
            if feature_payload is None:
                return {"reality_score": 0.5, "message": "Could not load image"}

            fft_result = feature_payload["results"]["fft"]
            noise_result = feature_payload["results"]["noise"]
            color_result = feature_payload["results"]["color"]
            ela_result = feature_payload["results"]["ela"]
            jpeg_result = feature_payload["results"]["jpeg"]
            metadata_result = feature_payload["results"]["metadata"]
            histogram_result = feature_payload["results"]["histogram"]
            edge_result = feature_payload["results"]["edge"]
            blur_result = feature_payload["results"]["blur"]
            forensic_vector = feature_payload["vector"]
            
            # Weighted scoring (more accurate than flat penalties)
            reality_score = 1.0
            findings = []
            
            if fft_result["anomaly"]:
                reality_score -= FORENSIC_WEIGHTS["fft"]
                findings.append(
                    f"FFT anomaly detected (peak={fft_result['peak_score']:.2f}, "
                    f"grid={fft_result['grid_score']:.2f}, hf_ratio={fft_result['hf_ratio']:.3f})"
                )
            
            if noise_result["suspicious"]:
                reality_score -= FORENSIC_WEIGHTS["noise"]
                findings.append(
                    f"Noise pattern suspicious (uniformity={noise_result['uniformity_score']:.3f}, "
                    f"level={noise_result['avg_noise_level']:.2f})"
                )
            
            if color_result["anomaly"]:
                reality_score -= FORENSIC_WEIGHTS["color"]
                findings.append(f"Color channel correlation anomaly (avg={color_result['avg_correlation']:.3f})")
            
            if ela_result["suspicious"] and not ela_result.get("skipped"):
                reality_score -= FORENSIC_WEIGHTS["ela"]
                findings.append(
                    f"ELA detected compression inconsistencies (score={ela_result['ela_score']:.2f}, "
                    f"bright pixels={ela_result['bright_pixel_ratio']:.2%})"
                )
            
            if jpeg_result["suspicious"] and not jpeg_result.get("skipped"):
                reality_score -= FORENSIC_WEIGHTS["jpeg"]
                findings.append(f"JPEG ghost detected (score={jpeg_result['ghost_score']:.2f})")
            
            if metadata_result.get("ai_detected"):
                reality_score -= FORENSIC_WEIGHTS["metadata"]
                findings.append(metadata_result["message"])
            elif metadata_result["status"] == "inconclusive":
                # Don't penalize missing EXIF
                findings.append(metadata_result["message"])
            
            if histogram_result["anomaly"]:
                reality_score -= FORENSIC_WEIGHTS["histogram"]
                findings.append(
                    f"Histogram anomaly (smoothness={histogram_result['avg_smoothness']:.6f}, "
                    f"clip_low={histogram_result['clip_low']:.3f}, clip_high={histogram_result['clip_high']:.3f})"
                )
            
            if edge_result["anomaly"]:
                reality_score -= FORENSIC_WEIGHTS["edge_coherence"]
                findings.append(
                    f"Edge pattern anomaly (density={edge_result['edge_density']:.3f}, "
                    f"uniformity={edge_result['edge_uniformity']:.3f})"
                )
            
            if blur_result["anomaly"]:
                reality_score -= FORENSIC_WEIGHTS["blur_consistency"]
                findings.append(
                    f"Blur consistency anomaly (uniformity={blur_result['blur_uniformity']:.3f}, "
                    f"range={blur_result['blur_range']:.1f})"
                )
            
            reality_score = max(0.0, min(1.0, reality_score))
            
            # ADDITIONAL: Weak signal aggregation
            # If multiple tests show "borderline" results, flag as suspicious
            weak_signals = 0
            
            # Check for borderline FFT
            if not fft_result["anomaly"] and (fft_result["peak_score"] > 1.8 or fft_result["grid_score"] > 1.2):
                weak_signals += 1
            
            # Check for borderline noise
            if not noise_result["suspicious"] and (noise_result["uniformity_score"] < 0.7 or noise_result["avg_noise_level"] < 4.5):
                weak_signals += 1
            
            # Check for borderline color
            if not color_result["anomaly"] and (color_result["avg_correlation"] > 0.95 or color_result["avg_correlation"] < 0.85):
                weak_signals += 1
            
            # Check for borderline histogram
            if not histogram_result["anomaly"] and histogram_result["avg_smoothness"] < 0.0001:
                weak_signals += 1
            
            # Check for borderline edge
            if not edge_result["anomaly"] and edge_result["edge_uniformity"] < 0.6:
                weak_signals += 1
            
            # Check for borderline blur
            if not blur_result["anomaly"] and blur_result["blur_uniformity"] < 0.35:
                weak_signals += 1
            
            # If 4+ weak signals, apply additional penalty
            if weak_signals >= 4:
                reality_score -= 0.15
                findings.append(f"Multiple borderline indicators detected ({weak_signals} weak signals)")
            elif weak_signals >= 3:
                reality_score -= 0.08
                findings.append(f"Several borderline indicators detected ({weak_signals} weak signals)")
            
            reality_score = max(0.0, min(1.0, reality_score))
            
            return {
                "reality_score": float(reality_score),
                "findings": findings if findings else ["No significant anomalies detected"],
                "details": {
                    "fft": fft_result,
                    "noise": noise_result,
                    "color": color_result,
                    "ela": ela_result,
                    "jpeg": jpeg_result,
                    "metadata": metadata_result,
                    "histogram": histogram_result,
                    "edge": edge_result,
                    "blur": blur_result
                },
                "forensic_vector": forensic_vector.tolist(),
                "feature_names": FORENSIC_FEATURE_NAMES
            }
        except Exception as e:
            return {"reality_score": 0.5, "message": f"Analysis error: {str(e)}"}
