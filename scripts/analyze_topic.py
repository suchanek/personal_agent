
import argparse
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from personal_agent.core.topic_classifier import TopicClassifier

def analyze_topic(text):
    """
    Analyzes the given text and returns the most relevant topic.
    """
    classifier = TopicClassifier()
    topics = classifier.classify(text)
    return topics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze the topic of a given string.")
    parser.add_argument("input_string", type=str, help="The string to analyze.")
    args = parser.parse_args()

    relevant_topics = analyze_topic(args.input_string)
    print(f"The relevant topic(s) for '{args.input_string}' is/are: {relevant_topics}")
