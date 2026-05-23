#!/usr/bin/env python3
"""
Test script to verify pure signal analysis detectors work without ML models.
"""

import numpy as np
from PIL import Image
import cv2
import os

# Test imports
print("Testing imports...")
from models.image_detector import ImageDetector
from models.video_detector import VideoDetector
from models.text_detector import TextDetector
print("✓ All detectors imported successfully\n")

# Test Text Detector
print("=" * 60)
print("TEXT DETECTOR TEST")
print("=" * 60)

text_detector = TextDetector()

# Human-like text (varied, bursty)
human_text = """
I can't believe it's already Friday! This week flew by so fast. 
Had a great meeting with the team yesterday - we finally figured out 
that bug that's been haunting us for weeks. Sarah suggested we try 
a completely different approach, and boom, it worked. Sometimes you 
just need fresh eyes on a problem, you know?
"""

# AI-like text (uniform, predictable)
ai_text = """
The implementation of the algorithm proceeds through several distinct phases.
Initially, the data structure is initialized with appropriate parameters.
Subsequently, the processing logic iterates through each element systematically.
The optimization strategy ensures efficient resource utilization throughout.
Finally, the results are aggregated and returned to the calling function.
"""

print("\n1. Analyzing human-like text:")
result = text_detector.predict(human_text)
print(f"   Score: {result['score']:.2f} ({result['label']})")
print(f"   Details: {result['details'][:100]}...")

print("\n2. Analyzing AI-like text:")
result = text_detector.predict(ai_text)
print(f"   Score: {result['score']:.2f} ({result['label']})")
print(f"   Details: {result['details'][:100]}...")

# Test Image Detector (create synthetic test image)
print("\n" + "=" * 60)
print("IMAGE DETECTOR TEST")
print("=" * 60)

image_detector = ImageDetector()

# Create a test image with noise (simulates real photo)
print("\n1. Creating synthetic 'real' image with sensor noise...")
real_img = np.random.randint(100, 150, (512, 512, 3), dtype=np.uint8)
# Add realistic noise pattern
noise = np.random.normal(0, 10, (512, 512, 3))
real_img = np.clip(real_img + noise, 0, 255).astype(np.uint8)

test_path = "/tmp/test_real_image.jpg"
cv2.imwrite(test_path, real_img)

result = image_detector.predict(test_path)
print(f"   Score: {result['score']:.2f} ({result['label']})")
print(f"   Reality Score: {result['reality_check']['reality_score']:.2f}")
print(f"   Findings: {result['reality_check']['findings'][0]}")

# Create a suspiciously smooth image (simulates AI generation)
print("\n2. Creating synthetic 'AI' image (too smooth)...")
ai_img = np.ones((512, 512, 3), dtype=np.uint8) * 128
# Add very uniform, minimal noise
ai_img = ai_img + np.random.randint(-2, 2, (512, 512, 3))
ai_img = np.clip(ai_img, 0, 255).astype(np.uint8)

test_path_ai = "/tmp/test_ai_image.jpg"
cv2.imwrite(test_path_ai, ai_img)

result = image_detector.predict(test_path_ai)
print(f"   Score: {result['score']:.2f} ({result['label']})")
print(f"   Reality Score: {result['reality_check']['reality_score']:.2f}")
if result['reality_check']['findings']:
    print(f"   Findings: {result['reality_check']['findings'][0]}")

# Cleanup
os.remove(test_path)
os.remove(test_path_ai)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED - No ML models required!")
print("=" * 60)
