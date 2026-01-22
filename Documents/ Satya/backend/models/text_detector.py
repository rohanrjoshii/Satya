from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class TextDetector:
    def __init__(self, model_name='roberta-base-openai-detector', device='cpu'):
        self.device = device
        # NOTE: 'roberta-base-openai-detector' is a placeholder. 
        # Real implementation would use a finetuned 'roberta-large' or 'microsoft/deberta-v3-base'.
        # For this skeleton, we use standard roberta-base and assume it's loaded as a classifier.
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("roberta-base")
            self.model = AutoModelForSequenceClassification.from_pretrained("roberta-base", num_labels=2)
            self.model.to(device)
            self.model.eval()
        except OSError:
             # Fallback if internet is not available or model is wrong
             # We create a dummy model for structure
             self.tokenizer = AutoTokenizer.from_pretrained("roberta-base")
             self.model = AutoModelForSequenceClassification.from_pretrained("roberta-base", num_labels=2)


    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            fake_prob = probs[0][1].item() # Assuming label 1 is 'Fake'
            
        # Statistical analysis logic (Bursty/Perplexity) would go here
        # Adding a dummy statistical factor for now
        stat_factor = 0.1 if len(text.split()) > 50 else 0.0 # Short text is harder to judge
        
        final_score = (fake_prob + stat_factor) / 1.1 # Normalize slightly
        final_score = min(final_score, 1.0)
        
        return {
            "score": final_score,
            "label": "AI-Generated" if final_score > 0.5 else "Human-Written",
            "details": f"Analysis based on {len(text.split())} words."
        }
