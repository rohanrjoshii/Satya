import re
import math
from collections import Counter, defaultdict

class TextDetector:
    """Pure statistical heuristics text detector - no ML models required."""

    FUNCTION_WORDS = {
        'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'it', 'for', 'on', 'with',
        'as', 'this', 'was', 'by', 'an', 'be', 'are', 'or', 'from', 'at', 'which', 'but',
        'not', 'have', 'has', 'had', 'were', 'their', 'they', 'them'
    }

    def __init__(self, model_name=None, device='cpu'):
        print("Text Detector initialized (statistical heuristics mode)")

    def calculate_perplexity_proxy(self, text):
        """
        AI text is statistically "too likely" - picks high-probability words.
        Approximate with character-level entropy.
        """
        if len(text) < 10:
            return 0.5
        
        # Character-level frequency
        char_counts = Counter(text.lower())
        total_chars = sum(char_counts.values())
        
        entropy = 0
        for count in char_counts.values():
            p = count / total_chars
            entropy -= p * math.log2(p)
        
        # Normalize (English text typically has ~4.5 bits/char entropy)
        # AI text tends to be slightly lower (~4.0-4.3)
        normalized = entropy / 4.5
        
        return {
            "entropy": float(entropy),
            "normalized": float(normalized),
            "suspicious": bool(entropy < 4.0)  # Too predictable
        }

    def calculate_burstiness(self, text):
        """
        Human writing has bursty vocabulary - use a word rarely, then cluster it.
        AI writing uses vocabulary more uniformly.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 20:
            return {"burstiness": 0.5, "suspicious": False}
        
        word_counts = Counter(words)
        
        # Calculate burstiness: variance of word frequencies
        frequencies = list(word_counts.values())
        mean_freq = sum(frequencies) / len(frequencies)
        variance = sum((f - mean_freq) ** 2 for f in frequencies) / len(frequencies)
        
        # Normalize by mean to get coefficient of variation
        burstiness = math.sqrt(variance) / (mean_freq + 1e-6)
        
        # Human text typically has burstiness > 2.0
        # AI text is more uniform (burstiness < 1.5)
        return {
            "burstiness": float(burstiness),
            "suspicious": bool(burstiness < 1.5)
        }

    def sentence_length_entropy(self, text):
        """
        AI tends toward uniform sentence lengths. Humans vary wildly.
        Compute entropy over sentence length distribution.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return {"entropy": 0.5, "suspicious": False}
        
        lengths = [len(s.split()) for s in sentences]
        
        # Bin lengths into categories
        bins = defaultdict(int)
        for length in lengths:
            bin_key = (length // 5) * 5  # Bins of 5 words
            bins[bin_key] += 1
        
        total = len(lengths)
        entropy = 0
        for count in bins.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        # Low entropy = suspiciously uniform
        return {
            "entropy": float(entropy),
            "avg_length": float(sum(lengths) / len(lengths)),
            "suspicious": bool(entropy < 1.5)
        }

    def lexical_richness(self, text):
        """
        AI writing in long texts has higher Type-Token Ratio (TTR).
        Measures unique words / total words in sliding windows.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 50:
            return {"ttr": 0.5, "suspicious": False}
        
        # Calculate TTR in sliding windows
        window_size = 50
        ttrs = []
        
        for i in range(0, len(words) - window_size, 10):
            window = words[i:i+window_size]
            unique = len(set(window))
            ttr = unique / window_size
            ttrs.append(ttr)
        
        if not ttrs:
            ttrs = [len(set(words)) / len(words)]
        
        avg_ttr = sum(ttrs) / len(ttrs)
        
        # AI text often has TTR > 0.75 (avoids repetition artificially)
        # Human text typically 0.5-0.7
        return {
            "ttr": float(avg_ttr),
            "suspicious": bool(avg_ttr > 0.75)
        }

    def punctuation_patterns(self, text):
        """
        AI text has suspiciously consistent punctuation usage.
        Humans are more erratic.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 5:
            return {"variance": 0.5, "suspicious": False}
        
        # Count commas per sentence
        comma_counts = [s.count(',') for s in sentences]
        
        if len(comma_counts) < 2:
            return {"variance": 0.5, "suspicious": False}
        
        mean_commas = sum(comma_counts) / len(comma_counts)
        variance = sum((c - mean_commas) ** 2 for c in comma_counts) / len(comma_counts)
        
        # Low variance = suspiciously consistent
        return {
            "variance": float(variance),
            "suspicious": bool(variance < 0.5)
        }

    def function_word_ratio(self, text):
        """
        AI-generated text often uses a less natural distribution of function words.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 20:
            return {"ratio": 0.5, "suspicious": False}

        function_count = sum(1 for w in words if w in self.FUNCTION_WORDS)
        ratio = function_count / len(words)

        # Natural English typically uses function words in the 35-55% range.
        return {
            "ratio": float(ratio),
            "suspicious": bool(ratio < 0.35 or ratio > 0.55)
        }

    def predict(self, text):
        """Run all statistical tests and aggregate results."""
        if len(text.strip()) < 20:
            return {
                "score": 0.5,
                "label": "Insufficient Text",
                "details": "Text too short for reliable analysis (minimum 20 characters).",
                "analysis": {}
            }
        
        # Run all checks
        perplexity = self.calculate_perplexity_proxy(text)
        burstiness = self.calculate_burstiness(text)
        sentence_entropy = self.sentence_length_entropy(text)
        lexical = self.lexical_richness(text)
        punctuation = self.punctuation_patterns(text)
        function_word = self.function_word_ratio(text)
        
        # Aggregate into AI likelihood score
        ai_score = 0.0
        findings = []
        
        if perplexity["suspicious"]:
            ai_score += 0.17
            findings.append(f"Low entropy detected (entropy={perplexity['entropy']:.2f})")
        
        if burstiness["suspicious"]:
            ai_score += 0.17
            findings.append(f"Uniform vocabulary distribution (burstiness={burstiness['burstiness']:.2f})")
        
        if sentence_entropy["suspicious"]:
            ai_score += 0.16
            findings.append(f"Suspiciously consistent sentence lengths (entropy={sentence_entropy['entropy']:.2f})")
        
        if lexical["suspicious"]:
            ai_score += 0.17
            findings.append(f"Elevated lexical diversity (TTR={lexical['ttr']:.2f})")
        
        if punctuation["suspicious"]:
            ai_score += 0.14
            findings.append(f"Consistent punctuation patterns (variance={punctuation['variance']:.2f})")
        
        if function_word["suspicious"]:
            ai_score += 0.19
            findings.append(f"Function word usage outside normal range (ratio={function_word['ratio']:.2f})")
        
        ai_score = min(1.0, ai_score)
        
        # Apply finer-grained category labels like QuillBot
        if ai_score >= 0.8:
            label = "Very Likely AI-Generated"
        elif ai_score >= 0.6:
            label = "Likely AI-Generated"
        elif ai_score >= 0.45:
            label = "Mixed signals"
        elif ai_score >= 0.25:
            label = "Likely Human-Written"
        else:
            label = "Very Likely Human-Written"

        # Generate explanation
        word_count = len(text.split())
        
        if ai_score < 0.3:
            details = f"Analysis of {word_count} words shows natural human writing patterns. "
            if findings:
                details += "Notes: " + "; ".join(findings)
            else:
                details += "Vocabulary burstiness, sentence variation, and word usage are all within normal human ranges."
        elif ai_score < 0.6:
            details = f"Analysis of {word_count} words shows mixed signals. "
            details += "Findings: " + "; ".join(findings) if findings else "The text has a few statistical anomalies."
        else:
            details = f"Analysis of {word_count} words shows strong AI-like signatures. "
            details += "Multiple red flags: " + "; ".join(findings)
        
        details += " This is a statistical estimate, not a definitive proof. Longer text generally gives more reliable signals."
        
        return {
            "score": float(ai_score),
            "label": label,
            "details": details,
            "analysis": {
                "word_count": word_count,
                "perplexity": perplexity,
                "burstiness": burstiness,
                "sentence_entropy": sentence_entropy,
                "lexical_richness": lexical,
                "punctuation": punctuation,
                "function_word": function_word
            }
        }
