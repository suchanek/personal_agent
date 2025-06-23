import re
from dataclasses import dataclass
from typing import Dict, List, Pattern

import yaml


@dataclass
class RuleSet:
    """Basic ruleset"""

    keywords: List[str]
    patterns: List[Pattern]


import re


class TopicClassifier:
    def __init__(self, config_path="topics.yaml"):
        self.load_config(config_path)
        self.stopwords = set(
            [
                "i",
                "have",
                "has",
                "had",
                "my",
                "is",
                "am",
                "was",
                "were",
                "the",
                "a",
                "an",
                "of",
                "in",
                "on",
                "and",
                "for",
                "with",
                "at",
                "to",
                "by",
                "from",
                "that",
                "this",
                "it",
                "as",
            ]
        )
        self.confidence_threshold = 0.1
        self.keyword_weight = 1
        self.phrase_weight = 3

    def load_config(self, config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.categories = config.get("categories", {})
            self.phrases = config.get("phrases", {})

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r"[^a-z\s]", "", text)
        tokens = text.split()
        tokens = [word for word in tokens if word not in self.stopwords]
        return " ".join(tokens)

    def classify(self, text, return_list=True):
        """
        Classify the topic(s) of a given text.

        Args:
            text (str): Text to classify
            return_list (bool): If True, returns list of topic names only.
                               If False, returns dict with confidence scores.

        Returns:
            Union[List[str], Dict[str, float]]: Topic classification results
        """
        cleaned = self.clean_text(text)
        raw_scores = {category: 0 for category in self.categories}

        # Check phrases first (higher weight)
        for category, phrases in self.phrases.items():
            if category in raw_scores:  # Make sure category exists in raw_scores
                for phrase in phrases:
                    if phrase.lower() in cleaned:
                        raw_scores[category] += self.phrase_weight

        # Check individual keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in cleaned:
                    raw_scores[category] += self.keyword_weight

        total_score = sum(raw_scores.values())
        if total_score == 0:
            return ["unknown"] if return_list else {"unknown": 0.0}

        normalized_scores = {
            cat: score / total_score for cat, score in raw_scores.items() if score > 0
        }
        high_confidence = {
            cat: round(score, 3)
            for cat, score in normalized_scores.items()
            if score >= self.confidence_threshold
        }

        if not high_confidence:
            return ["unknown"] if return_list else {"unknown": 0.0}

        if return_list:
            return list(high_confidence.keys())
        else:
            return high_confidence


if __name__ == "__main__":
    classifier = TopicClassifier()
    examples = [
        "My name is John and I work at Google.",
        "I love to play the piano and travel.",
        "I am 35 years old and live in Paris.",
        "I studied biology at university.",
        "Married to a wonderful woman with 2 kids.",
        "I prefer coffee over tea.",
        "I plan to climb Mount Everest.",
        "I have a peanut allergy.",
        "I have a dog named Max and love animals.",
        "I enjoy hiking and playing tennis on weekends.",
        "Completely unrelated sentence.",
    ]

    print("=== Topic Classification Demo ===")
    for text in examples:
        # Production mode: returns list of topics
        topics_list = classifier.classify(text)
        # Development mode: returns dict with confidence scores
        topics_scores = classifier.classify(text, return_list=False)

        print(f"Input: {text}")
        print(f"Topics (list): {topics_list}")
        print(f"Topics (scores): {topics_scores}\n")
