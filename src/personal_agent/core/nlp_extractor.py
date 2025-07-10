
import spacy
from typing import List, Dict, Tuple, Any

# Load the small English model
# This should be run once at module load or application startup
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> List[Dict[str, str]]:
    """
    Extracts named entities from text using spaCy.
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})
    return entities

def extract_relationships(text: str) -> List[Tuple[str, str, str]]:
    """
    Extracts simple subject-verb-object relationships from text using spaCy's dependency parser.
    This version includes improved coreference resolution and entity linking.
    """
    doc = nlp(text)
    relationships = []
    
    # Get entities to help with linking
    entities = {ent.text: ent.label_ for ent in doc.ents}
    entity_texts = list(entities.keys())
    
    # Simple coreference resolution
    last_person = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            last_person = ent.text

    for sent in doc.sents:
        for token in sent:
            # Find verbs that are likely to form relationships
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ in ("nsubj", "nsubjpass")]
                objects = [child for child in token.children if child.dep_ in ("dobj", "attr", "pobj")]
                
                # Also look for prepositional objects for "works at", "lives in" patterns
                prep_objects = []
                for child in token.children:
                    if child.dep_ == "prep":
                        for grandchild in child.children:
                            if grandchild.dep_ == "pobj":
                                prep_objects.append((child.text, grandchild))
                
                if subjects and (objects or prep_objects):
                    subject = subjects[0]
                    
                    subject_text = subject.text
                    # Resolve pronouns
                    if subject.pos_ == "PRON" and last_person:
                        subject_text = last_person
                    
                    # Use the full entity text if available
                    for ent_text in entity_texts:
                        if subject.text.lower() in ent_text.lower() or ent_text.lower() in subject.text.lower():
                            subject_text = ent_text
                            break
                    
                    # Handle direct objects
                    if objects:
                        obj = objects[0]
                        object_text = obj.text
                        for ent_text in entity_texts:
                            if obj.text.lower() in ent_text.lower() or ent_text.lower() in obj.text.lower():
                                object_text = ent_text
                                break
                        
                        relation_text = token.lemma_
                        relationships.append((subject_text, relation_text, object_text))
                    
                    # Handle prepositional objects (e.g., "works at Google", "lives in Mountain View")
                    for prep, pobj in prep_objects:
                        object_text = pobj.text
                        for ent_text in entity_texts:
                            if pobj.text.lower() in ent_text.lower() or ent_text.lower() in pobj.text.lower():
                                object_text = ent_text
                                break
                        
                        relation_text = f"{token.lemma_} {prep}"
                        relationships.append((subject_text, relation_text, object_text))
                    
                    # Update last seen person for coreference
                    if subject.text in entities and entities[subject.text] == "PERSON":
                        last_person = subject.text

    return relationships

if __name__ == "__main__":
    # Example Usage
    text1 = "Eric works at Google. He lives in Mountain View."
    text2 = "Emma is a yoga instructor. She has a dog named Max."
    text3 = "My favorite programming language is Python."
    text4 = "John Doe is the CEO of Example Corp."

    print("--- Entities ---")
    print(f"Text: {text1}")
    print(extract_entities(text1))
    print(f"Text: {text2}")
    print(extract_entities(text2))
    print(f"Text: {text3}")
    print(extract_entities(text3))
    print(f"Text: {text4}")
    print(extract_entities(text4))

    print("\n--- Relationships ---")
    print(f"Text: {text1}")
    print(extract_relationships(text1))
    print(f"Text: {text2}")
    print(extract_relationships(text2))
    print(f"Text: {text3}")
    print(extract_relationships(text3))
    print(f"Text: {text4}")
    print(extract_relationships(text4))
