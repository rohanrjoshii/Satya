import torch
from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO

class ImageDetector:
    def __init__(self, device='cpu'):
        self.pipe = None
        try:
            print("Loading Image Detection Model...")
            # Trying a different model known for AI detection
            self.pipe = pipeline("image-classification", model="umm-maybe/AI-image-detector", device=-1 if device=='cpu' else 0)
            print("Model Loaded Successfully!")
        except Exception as e:
            print(f"Failed to load primary model: {e}")
            print("Using fallback logic.")

    def predict(self, image_path_or_url):
        if not self.pipe:
            return {
                "score": 0.5,
                "label": "Model Error",
                "details": "The AI detection model could not be loaded. Please check server logs."
            }

        try:
            # Handle URL vs File Path
            if image_path_or_url.startswith('http'):
                response = requests.get(image_path_or_url, timeout=10)
                image = Image.open(BytesIO(response.content)).convert('RGB')
            else:
                image = Image.open(image_path_or_url).convert('RGB')
            
            # Predict
            results = self.pipe(image)
            # Result format: [{'label': 'artificial', 'score': 0.9}, {'label': 'human', 'score': 0.1}]
            
            # Parse top result
            top_result = results[0]
            label = top_result['label']
            score = top_result['score']
            
            ai_likelihood = score
            if label.lower() in ['human', 'real', 'authentic']:
                ai_likelihood = 1.0 - score
            
            return {
                "score": ai_likelihood,
                "label": "AI-Generated" if ai_likelihood > 0.5 else "Real",
                "details": f"Model identified as {label} with {score*100:.1f}% confidence."
            }
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                "score": 0.5,
                "label": "Error", 
                "details": f"Processing failed: {str(e)}"
            }

