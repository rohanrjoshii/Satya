import os
import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from utils.reality_checker import RealityChecker

HAS_TORCH = False
HAS_ONNXRUNTIME = False
HybridImageClassifier = None

try:
    import torch
    from torchvision import transforms
    from models.hybrid_image_model import HybridImageClassifier
    HAS_TORCH = True
except Exception as e:
    print(f"[ImageDetector] Warning: PyTorch/timm unavailable: {e}")

try:
    import onnxruntime as ort
    HAS_ONNXRUNTIME = True
except Exception as e:
    print(f"[ImageDetector] Warning: ONNX Runtime unavailable: {e}")

class ImageDetector:
    """Hybrid image detector combining forensic heuristics and deep learning."""

    def __init__(
        self,
        device='cpu',
        model_path: str | None = None,
        onnx_path: str | None = None,
        backbone: str = 'tf_efficientnet_b4_ns',
        hidden_dim: int = 768,
        use_freq_branch: bool = True,
    ):
        self.device = device
        self.reality_checker = RealityChecker(device=device)
        self.model = None
        self.onnx_session = None
        self.transforms = self._build_transforms() if HAS_TORCH else None
        self.use_ml = HAS_TORCH and HybridImageClassifier is not None
        self.use_freq_branch = use_freq_branch

        if self.use_ml:
            self._load_model(model_path=model_path, onnx_path=onnx_path, backbone=backbone, hidden_dim=hidden_dim)
        else:
            print("[ImageDetector] Running in pure forensic fallback mode.")

        print("Image Detector initialized (hybrid inference mode)" if self.use_ml else "Image Detector initialized (forensic only mode)")

    def _build_transforms(self):
        return transforms.Compose([
            transforms.Resize((384, 384)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _load_model(self, model_path: str | None, onnx_path: str | None, backbone: str, hidden_dim: int):
        if onnx_path and os.path.exists(onnx_path) and HAS_ONNXRUNTIME:
            self.onnx_session = ort.InferenceSession(onnx_path)
            print(f"[ImageDetector] Loaded ONNX model from {onnx_path}")
            return

        if not self.use_ml:
            return

        forensic_dim = 17
        self.model = HybridImageClassifier(
            forensic_dim=forensic_dim,
            backbone_name=backbone,
            hidden_dim=hidden_dim,
            use_freq_branch=self.use_freq_branch,
        )
        self.model.to(self.device)

        if model_path and os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                    checkpoint = checkpoint['state_dict']
                self.model.load_state_dict(checkpoint)
                self.model.eval()
                print(f"[ImageDetector] Loaded PyTorch checkpoint from {model_path}")
            except Exception as e:
                print(f"[ImageDetector] Warning: Failed to load PyTorch checkpoint: {e}")
        else:
            self.model.eval()
            print("[ImageDetector] No checkpoint found, using fresh hybrid model weights.")

    def _load_image_from_source(self, image_path_or_url: str):
        if image_path_or_url.startswith('http'):
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerifAI/1.0; +https://localhost)",
                "Accept": "image/*,*/*;q=0.8",
            }
            response = requests.get(image_path_or_url, timeout=30, headers=headers, allow_redirects=True)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert('RGB')
            temp_path = f"/tmp/verifai_{os.getpid()}_analysis.jpg"
            image.save(temp_path)
            return image, temp_path

        image = Image.open(image_path_or_url).convert('RGB')
        return image, image_path_or_url

    def _prepare_image_tensor(self, image: Image.Image):
        if not self.use_ml or self.transforms is None:
            raise RuntimeError("PyTorch is required for deep learning inference.")
        tensor = self.transforms(image).unsqueeze(0)
        return tensor.to(self.device)

    def _predict_ml(self, image_tensor, forensic_vector: np.ndarray):
        if self.onnx_session is not None:
            inputs = self.onnx_session.get_inputs()
            if len(inputs) != 2:
                raise RuntimeError("ONNX model must accept image and forensic feature inputs.")
            ort_inputs = {
                inputs[0].name: image_tensor.cpu().numpy().astype(np.float32),
                inputs[1].name: forensic_vector.reshape(1, -1).astype(np.float32),
            }
            output = self.onnx_session.run(None, ort_inputs)
            return float(output[0].squeeze())

        with torch.no_grad():
            forensic_tensor = torch.from_numpy(forensic_vector).unsqueeze(0).to(self.device)
            prediction = self.model(image_tensor, forensic_tensor)
            return float(prediction.squeeze().cpu().numpy())

    def _blend_scores(self, forensic_score: float, ml_score: float, metadata_flag: bool):
        alpha = 0.65 if metadata_flag else 0.75
        return float(max(0.0, min(1.0, ml_score * alpha + forensic_score * (1.0 - alpha))))

    def make_label(self, score: float):
        if score >= 0.90:
            return "AI-Generated"
        if score >= 0.55:
            return "Suspicious"
        return "Real"

    def predict(self, image_path_or_url: str, use_ml: bool = True):
        try:
            image, image_path = self._load_image_from_source(image_path_or_url)
            reality_result = self.reality_checker.perform_full_check(image_path)
            forensic_score = 1.0 - float(reality_result.get("reality_score", 0.5))
            fused_score = forensic_score
            ml_score = None
            model_side = "forensic"

            if use_ml and self.use_ml and (self.model is not None or self.onnx_session is not None):
                forensic_vector = np.array(reality_result.get("forensic_vector", []), dtype=np.float32)
                if forensic_vector.size == 0:
                    raise RuntimeError("Forensic vector could not be extracted.")
                image_tensor = self._prepare_image_tensor(image)
                ml_score = self._predict_ml(image_tensor, forensic_vector)
                metadata_flag = bool(forensic_vector[9] > 0.5)
                fused_score = self._blend_scores(forensic_score, ml_score, metadata_flag)
                model_side = "hybrid"

            explanation = self.generate_explanation(
                fused_score,
                reality_result.get("findings", []),
                ml_score=ml_score,
                forensic_score=forensic_score,
            )

            return {
                "score": float(fused_score),
                "label": self.make_label(fused_score),
                "details": explanation,
                "analysis": {
                    "forensic_score": float(forensic_score),
                    "ml_score": float(ml_score) if ml_score is not None else None,
                    "model_type": model_side,
                    "findings": reality_result.get("findings", []),
                    "feature_names": reality_result.get("feature_names"),
                },
                "reality_check": reality_result,
            }
        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                "score": 0.5,
                "label": "Error",
                "details": f"Processing failed: {str(e)}"
            }

    def predict_batch(self, image_paths_or_urls: list[str], use_ml: bool = True):
        return [self.predict(item, use_ml=use_ml) for item in image_paths_or_urls]

    def export_onnx(self, output_path: str, image_size=(384, 384)):
        if not self.use_ml or self.model is None:
            raise RuntimeError("PyTorch is required to export ONNX.")
        self.model.eval()
        dummy_image = torch.randn(1, 3, image_size[0], image_size[1], device=self.device)
        dummy_forensic = torch.randn(1, len(self.reality_checker.get_forensic_feature_vector('/tmp')['vector']), device=self.device)
        torch.onnx.export(
            self.model,
            (dummy_image, dummy_forensic),
            output_path,
            opset_version=17,
            input_names=["image", "forensic_features"],
            output_names=["score"],
            dynamic_axes={
                "image": {0: "batch_size"},
                "forensic_features": {0: "batch_size"},
                "score": {0: "batch_size"},
            },
        )
        print(f"[ImageDetector] Exported ONNX model to {output_path}")

    def generate_explanation(self, score, findings, ml_score=None, forensic_score=None):
        if score < 0.20:
            base = "High confidence in authenticity. "
        elif score < 0.50:
            base = "Likely authentic. "
        elif score < 0.80:
            base = "Suspicious patterns detected. "
        else:
            base = "Critical anomalies detected. "

        if findings:
            base += "Forensic evidence: " + "; ".join(findings)

        if ml_score is not None:
            base += f" | Deep model score: {ml_score:.3f}."

        if forensic_score is not None:
            base += f" Forensic score: {forensic_score:.3f}."

        return base

