import re
from dataclasses import dataclass
from typing import Dict, List, Pattern


@dataclass
class RuleSet:
    keywords: List[str]
    patterns: List[Pattern]


class TopicClassifier:
    """Enhanced rule-based topic classifier that doesn't require an LLM."""

    def __init__(self):
        self.TOPIC_RULES: Dict[str, RuleSet] = {
            "personal_info": RuleSet(
                keywords=[
                    "name",
                    "age",
                    "birthday",
                    "born",
                    "live",
                    "from",
                    "address",
                    "phone",
                    "email",
                ],
                patterns=[
                    re.compile(r"\bmy name is\b", re.IGNORECASE),
                    re.compile(r"\bi (?:am|\'m) \d+\b", re.IGNORECASE),
                    re.compile(r"\bi live in\b", re.IGNORECASE),
                    re.compile(r"\bi\'m from\b", re.IGNORECASE),
                ],
            ),
            "work": RuleSet(
                keywords=[
                    "work",
                    "job",
                    "career",
                    "company",
                    "office",
                    "boss",
                    "colleague",
                    "salary",
                    "employed",
                    "unemployed",
                ],
                patterns=[
                    re.compile(r"\bi work at\b", re.IGNORECASE),
                    re.compile(r"\bmy job\b", re.IGNORECASE),
                    re.compile(r"\bi(?:'m| am) a\b", re.IGNORECASE),
                    re.compile(r"\bwork as\b", re.IGNORECASE),
                ],
            ),
            "education": RuleSet(
                keywords=[
                    "school",
                    "university",
                    "college",
                    "degree",
                    "study",
                    "student",
                    "graduate",
                    "major",
                    "course",
                ],
                patterns=[
                    re.compile(r"\bi study\b", re.IGNORECASE),
                    re.compile(r"\bi graduated\b", re.IGNORECASE),
                    re.compile(r"\bmy degree\b", re.IGNORECASE),
                    re.compile(r"\bi(?:'m| am) studying\b", re.IGNORECASE),
                ],
            ),
            "family": RuleSet(
                keywords=[
                    "family",
                    "parent",
                    "mother",
                    "father",
                    "mom",
                    "dad",
                    "sibling",
                    "brother",
                    "sister",
                    "child",
                    "kids",
                    "married",
                    "spouse",
                    "wife",
                    "husband",
                ],
                patterns=[
                    re.compile(r"\bmy family\b", re.IGNORECASE),
                    re.compile(r"\bmy parents\b", re.IGNORECASE),
                    re.compile(r"\bi have \d+ kids\b", re.IGNORECASE),
                    re.compile(r"\bmarried to\b", re.IGNORECASE),
                ],
            ),
            "hobbies": RuleSet(
                keywords=[
                    "hobby",
                    "enjoy",
                    "love",
                    "like",
                    "play",
                    "watch",
                    "read",
                    "listen",
                    "music",
                    "sport",
                    "game",
                    "travel",
                ],
                patterns=[
                    re.compile(r"\bi enjoy\b", re.IGNORECASE),
                    re.compile(r"\bi love\b", re.IGNORECASE),
                    re.compile(r"\bi like to\b", re.IGNORECASE),
                    re.compile(r"\bmy hobby\b", re.IGNORECASE),
                ],
            ),
            "preferences": RuleSet(
                keywords=[
                    "prefer",
                    "favorite",
                    "favourite",
                    "best",
                    "worst",
                    "hate",
                    "dislike",
                    "can't stand",
                ],
                patterns=[
                    re.compile(r"\bi prefer\b", re.IGNORECASE),
                    re.compile(r"\bmy favorite\b", re.IGNORECASE),
                    re.compile(r"\bi hate\b", re.IGNORECASE),
                    re.compile(r"\bi don't like\b", re.IGNORECASE),
                ],
            ),
            "health": RuleSet(
                keywords=[
                    "health",
                    "doctor",
                    "medicine",
                    "sick",
                    "illness",
                    "allergy",
                    "diet",
                    "exercise",
                    "gym",
                ],
                patterns=[
                    re.compile(r"\bi have\b", re.IGNORECASE),
                    re.compile(r"\ballergic to\b", re.IGNORECASE),
                    re.compile(r"\bmy doctor\b", re.IGNORECASE),
                    re.compile(r"\bi exercise\b", re.IGNORECASE),
                ],
            ),
            "location": RuleSet(
                keywords=[
                    "city",
                    "town",
                    "country",
                    "state",
                    "neighborhood",
                    "address",
                    "zip",
                    "postal",
                ],
                patterns=[
                    re.compile(r"\bi live in\b", re.IGNORECASE),
                    re.compile(r"\blocated in\b", re.IGNORECASE),
                    re.compile(r"\bfrom\b", re.IGNORECASE),
                    re.compile(r"\bzip code\b", re.IGNORECASE),
                ],
            ),
            "goals": RuleSet(
                keywords=[
                    "goal",
                    "plan",
                    "want",
                    "hope",
                    "dream",
                    "aspire",
                    "achieve",
                    "target",
                ],
                patterns=[
                    re.compile(r"\bmy goal\b", re.IGNORECASE),
                    re.compile(r"\bi want to\b", re.IGNORECASE),
                    re.compile(r"\bi plan to\b", re.IGNORECASE),
                    re.compile(r"\bi hope to\b", re.IGNORECASE),
                ],
            ),
            "general": RuleSet(keywords=[], patterns=[]),
        }

    def normalize(self, text: str) -> str:
        """Basic text normalization."""
        return re.sub(r"\s+", " ", text.lower()).strip()

    def classify_topic(self, text: str) -> List[str]:
        """
        Classify the topic(s) of a given text using rule-based classification.

        :param text: Text to classify
        :return: List of topic categories
        """
        text_normalized = self.normalize(text)
        topics = []

        for topic, rules in self.TOPIC_RULES.items():
            if topic == "general":
                continue

            keyword_matches = sum(
                1 for keyword in rules.keywords if keyword in text_normalized
            )
            pattern_matches = sum(
                1 for pattern in rules.patterns if pattern.search(text_normalized)
            )

            score = keyword_matches * 1 + pattern_matches * 2

            if score >= 2:
                topics.append(topic)

        if not topics:
            topics = ["general"]

        return topics
