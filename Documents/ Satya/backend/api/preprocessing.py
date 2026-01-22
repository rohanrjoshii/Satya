# Preprocessing utilities for cleaning text, resizing images, etc.
import cv2
import re

def clean_text(text: str) -> str:
    # Remove special chars, simple normalization
    return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()

def preprocess_image(image_path, size=(224, 224)):
    img = cv2.imread(image_path)
    img = cv2.resize(img, size)
    return img
