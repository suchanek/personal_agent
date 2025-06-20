import re
from dataclasses import dataclass
from typing import Dict, List, Pattern


@dataclass
class RuleSet:
    """Basic ruleset"""

    keywords: List[str]
    patterns: List[Pattern]


class TopicClassifier:
    """Enhanced rule-based topic classifier for categorizing text without requiring an LLM.

    This classifier uses a combination of keyword matching and regex pattern matching
    to categorize text into predefined topics. It's designed to identify personal
    information categories such as work, education, family, hobbies, and more.

    The classifier employs a scoring system where:
    - Keyword matches contribute 1 point each
    - Pattern matches contribute 2 points each
    - A minimum score of 2 is required for topic classification
    - If no topics meet the threshold, text is classified as "general"

    Attributes:
        TOPIC_RULES (Dict[str, RuleSet]): Dictionary mapping topic names to their
            corresponding RuleSet objects containing keywords and regex patterns.

    Supported Topics:
        - personal_info: Name, age, contact information, location details
        - work: Job, career, company, employment-related information
        - education: School, university, degrees, academic information
        - family: Family members, relationships, marital status
        - hobbies: Interests, activities, entertainment preferences
        - preferences: Likes, dislikes, favorites, opinions
        - health: Medical information, allergies, fitness, diet
        - location: Geographic information, addresses, places
        - goals: Aspirations, plans, targets, future objectives
        - general: Fallback category for unclassified text

    Example:
        >>> classifier = TopicClassifier()
        >>> topics = classifier.classify_topic("My name is John and I work at Google")
        >>> print(topics)
        ['personal_info', 'work']

        >>> topics = classifier.classify_topic("I love playing piano and traveling")
        >>> print(topics)
        ['hobbies']

        >>> topics = classifier.classify_topic("Random unrelated text")
        >>> print(topics)
        ['general']

    Note:
        This classifier is rule-based and deterministic. It doesn't learn from data
        but relies on predefined patterns and keywords. It is designed to be efficient
    """

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
                    "studied",
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
                    "grandma",
                    "grandpa",
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
            "feelings": RuleSet(
                keywords=[
                    "happy",
                    "sad",
                    "angry",
                    "frustrated",
                    "excited",
                    "nervous",
                    "worried",
                    "anxious",
                    "depressed",
                    "mood",
                    "emotion",
                    "feel",
                    "feeling",
                ],
                patterns=[
                    re.compile(r"\bi feel\b", re.IGNORECASE),
                    re.compile(r"\bi am feeling\b", re.IGNORECASE),
                    re.compile(r"\bi'm feeling\b", re.IGNORECASE),
                ],
            ),
            "general": RuleSet(keywords=[], patterns=[]),
        }

    def normalize(self, _text: str) -> str:
        """Basic text normalization."""
        return re.sub(r"\s+", " ", _text.lower()).strip()

    def classify_topic(self, _text: str) -> List[str]:
        """
        Classify the topic(s) of a given text using rule-based classification.

        :param text: Text to classify
        :return: List of topic categories
        """
        text_normalized = self.normalize(_text)
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
        "Completely unrelated sentence.",
    ]

    for text in examples:
        topics = classifier.classify_topic(text)
        print(f"Input: {text}\nTopics: {topics}\n")
