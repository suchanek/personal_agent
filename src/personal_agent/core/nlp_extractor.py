
import spacy
import re
from typing import List, Dict, Tuple, Any

# Load the small English model
# This should be run once at module load or application startup
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def is_meaningful_entity(entity_text: str, entity_label: str) -> bool:
    """
    Filter out meaningless entities like page numbers, standalone years, etc.
    
    Args:
        entity_text: The text of the entity
        entity_label: The spaCy label of the entity
        
    Returns:
        True if the entity is meaningful for relationship building
    """
    # Skip page references (pp 123, p. 456, etc.)
    if re.match(r'^pp?\s*\.?\s*\d+', entity_text.lower()):
        return False
    
    # Skip page ranges (123-456, 5992–599, etc.)
    if re.match(r'^\d+[-–]\d+$', entity_text):
        return False
    
    # Skip standalone years (1986, 2000, etc.) unless they're part of a larger context
    if re.match(r'^\d{4}$', entity_text) and entity_label == "DATE":
        return False
    
    # Skip standalone numbers unless they're cardinal numbers in context
    if re.match(r'^\d+$', entity_text) and entity_label not in ["PERSON", "ORG", "GPE"]:
        return False
    
    # Skip very short entities (< 2 chars) unless they're important types
    if len(entity_text) < 2 and entity_label not in ["PERSON", "ORG", "GPE"]:
        return False
    
    # Skip common stop words that might be extracted as entities
    stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    if entity_text.lower() in stop_words:
        return False
    
    # Skip volume/issue references (Vol 25, Issue 20, etc.)
    if re.match(r'^(vol|volume|issue|no)\s*\.?\s*\d+', entity_text.lower()):
        return False
    
    # Keep meaningful entities
    return True

def extract_entities(text: str) -> List[Dict[str, str]]:
    """
    Extracts meaningful named entities from text using spaCy with filtering.
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if is_meaningful_entity(ent.text, ent.label_):
            entities.append({"text": ent.text, "label": ent.label_})
    return entities

def is_meaningful_relationship(subject: str, relation: str, obj: str) -> bool:
    """
    Filter out meaningless relationships.
    
    Args:
        subject: Subject of the relationship
        relation: Relationship type
        obj: Object of the relationship
        
    Returns:
        True if the relationship is meaningful for knowledge graph
    """
    # Skip relationships with meaningless entities
    if not subject or not obj or subject.strip() == "" or obj.strip() == "":
        return False
    
    # Skip relationships with unresolved pronouns
    pronouns = {'he', 'she', 'it', 'they', 'him', 'her', 'them', 'his', 'hers', 'its', 'their'}
    if subject.lower() in pronouns or obj.lower() in pronouns:
        return False
    
    # Skip relationships with page numbers, years, etc.
    if not is_meaningful_entity(subject, "MISC") or not is_meaningful_entity(obj, "MISC"):
        return False
    
    # Skip very generic relationships that don't add value
    generic_relations = {'be', 'have', 'do', 'get', 'make', 'take', 'come', 'go'}
    if relation.lower() in generic_relations and len(obj) < 3:
        return False
    
    # Keep meaningful relationships
    return True

def extract_relationships(text: str) -> List[Tuple[str, str, str]]:
    """
    Extracts meaningful subject-verb-object relationships from text using spaCy's dependency parser.
    This version includes improved coreference resolution, entity linking, and relationship filtering.
    """
    doc = nlp(text)
    relationships = []
    
    # Get meaningful entities to help with linking
    meaningful_entities = {}
    entity_texts = []
    for ent in doc.ents:
        if is_meaningful_entity(ent.text, ent.label_):
            meaningful_entities[ent.text] = ent.label_
            entity_texts.append(ent.text)
    
    # Simple coreference resolution
    last_person = None
    for ent_text, ent_label in meaningful_entities.items():
        if ent_label == "PERSON":
            last_person = ent_text

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
                        
                        # Only add meaningful relationships
                        if is_meaningful_relationship(subject_text, relation_text, object_text):
                            relationships.append((subject_text, relation_text, object_text))
                    
                    # Handle prepositional objects (e.g., "works at Google", "lives in Mountain View")
                    for prep, pobj in prep_objects:
                        object_text = pobj.text
                        for ent_text in entity_texts:
                            if pobj.text.lower() in ent_text.lower() or ent_text.lower() in pobj.text.lower():
                                object_text = ent_text
                                break
                        
                        relation_text = f"{token.lemma_} {prep}"
                        
                        # Only add meaningful relationships
                        if is_meaningful_relationship(subject_text, relation_text, object_text):
                            relationships.append((subject_text, relation_text, object_text))
                    
                    # Update last seen person for coreference
                    if subject.text in meaningful_entities and meaningful_entities[subject.text] == "PERSON":
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
