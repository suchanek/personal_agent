"""
Unit tests for AgentFactManager (formerly AgentKnowledgeManager).

This module tests the fact management functionality
extracted from the AgnoPersonalAgent class using Python's built-in unittest framework.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# from unittest.mock import MagicMock, Mock, mock_open

from src.personal_agent.core.agent_knowledge_manager import AgentFactManager


class TestAgentFactManager(unittest.TestCase):
    """Test cases for AgentFactManager."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.user_id = "test_user"
        self.storage_dir = "/tmp/test_storage"
        self.lightrag_url = "http://localhost:9620"
        self.lightrag_memory_url = "http://localhost:9621"

        # Use a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        self.manager = AgentFactManager(
            user_id=self.user_id,
            storage_dir=self.temp_dir,
            lightrag_url=self.lightrag_url,
            lightrag_memory_url=self.lightrag_memory_url,
        )

    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary files
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test AgentFactManager initialization."""
        self.assertEqual(self.manager.user_id, self.user_id)
        self.assertEqual(self.manager.storage_dir, self.temp_dir)
        self.assertEqual(self.manager.lightrag_url, self.lightrag_url)
        self.assertEqual(self.manager.lightrag_memory_url, self.lightrag_memory_url)

        # Check that knowledge base file path is set correctly
        expected_kb_file = os.path.join(self.temp_dir, f"{self.user_id}_knowledge.json")
        self.assertEqual(self.manager.knowledge_base_file, expected_kb_file)

        # Check that knowledge base is initialized
        self.assertIsInstance(self.manager.knowledge_base, dict)
        self.assertIn("facts", self.manager.knowledge_base)
        self.assertIn("preferences", self.manager.knowledge_base)
        self.assertIn("entities", self.manager.knowledge_base)
        self.assertIn("relationships", self.manager.knowledge_base)
        self.assertIn("metadata", self.manager.knowledge_base)

    def test_init_without_lightrag_urls(self):
        """Test initialization without LightRAG URLs."""
        manager = AgentFactManager(user_id="test_user", storage_dir="/tmp/test")

        self.assertIsNone(manager.lightrag_url)
        self.assertIsNone(manager.lightrag_memory_url)

    def test_load_knowledge_base_new_file(self):
        """Test loading knowledge base when file doesn't exist."""
        # The knowledge base should be created with default structure
        kb = self.manager.knowledge_base

        self.assertIsInstance(kb, dict)
        self.assertEqual(kb["facts"], [])
        self.assertEqual(kb["preferences"], {})
        self.assertEqual(kb["entities"], {})
        self.assertEqual(kb["relationships"], [])
        self.assertIn("version", kb["metadata"])
        self.assertEqual(kb["metadata"]["version"], "1.0")

    def test_load_knowledge_base_existing_file(self):
        """Test loading knowledge base from existing file."""
        # Create a test knowledge base file
        test_kb = {
            "facts": [{"text": "Test fact", "source": "user"}],
            "preferences": {"ui": {"theme": "dark"}},
            "entities": {"John": {"type": "person"}},
            "relationships": [
                {"entity1": "John", "relation": "works_at", "entity2": "Company"}
            ],
            "metadata": {"version": "1.0", "last_updated": "2023-01-01"},
        }

        kb_file = os.path.join(self.temp_dir, f"{self.user_id}_knowledge.json")
        with open(kb_file, "w") as f:
            json.dump(test_kb, f)

        # Create a new manager that should load the existing file
        manager = AgentFactManager(user_id=self.user_id, storage_dir=self.temp_dir)

        self.assertEqual(len(manager.knowledge_base["facts"]), 1)
        self.assertEqual(manager.knowledge_base["facts"][0]["text"], "Test fact")
        self.assertEqual(manager.knowledge_base["preferences"]["ui"]["theme"], "dark")
        self.assertIn("John", manager.knowledge_base["entities"])

    def test_load_knowledge_base_corrupted_file(self):
        """Test loading knowledge base when file is corrupted."""
        # Create a corrupted JSON file
        kb_file = os.path.join(self.temp_dir, f"{self.user_id}_knowledge.json")
        with open(kb_file, "w") as f:
            f.write("invalid json content")

        # Create a new manager that should handle the corrupted file gracefully
        manager = AgentFactManager(user_id=self.user_id, storage_dir=self.temp_dir)

        # Should fall back to default structure
        self.assertIsInstance(manager.knowledge_base, dict)
        self.assertEqual(manager.knowledge_base["facts"], [])

    def test_save_knowledge_base(self):
        """Test saving knowledge base to file."""
        # Add some data to the knowledge base
        self.manager.knowledge_base["facts"].append(
            {"text": "Test fact", "source": "user"}
        )

        # Save the knowledge base
        result = self.manager._save_knowledge_base()

        self.assertTrue(result)

        # Verify the file was created and contains the data
        self.assertTrue(os.path.exists(self.manager.knowledge_base_file))

        with open(self.manager.knowledge_base_file, "r") as f:
            saved_kb = json.load(f)

        self.assertEqual(len(saved_kb["facts"]), 1)
        self.assertEqual(saved_kb["facts"][0]["text"], "Test fact")
        self.assertIsNotNone(saved_kb["metadata"]["last_updated"])

    def test_save_knowledge_base_with_custom_data(self):
        """Test saving custom knowledge base data."""
        custom_kb = {
            "facts": [{"text": "Custom fact", "source": "test"}],
            "preferences": {},
            "entities": {},
            "relationships": [],
            "metadata": {"version": "1.0"},
        }

        result = self.manager._save_knowledge_base(custom_kb)

        self.assertTrue(result)

        # Verify the custom data was saved
        with open(self.manager.knowledge_base_file, "r") as f:
            saved_kb = json.load(f)

        self.assertEqual(saved_kb["facts"][0]["text"], "Custom fact")

    def test_add_fact(self):
        """Test adding a fact to the knowledge base."""
        result = self.manager.add_fact("Test fact", "user", 0.9)

        self.assertTrue(result)
        self.assertEqual(len(self.manager.knowledge_base["facts"]), 1)

        fact = self.manager.knowledge_base["facts"][0]
        self.assertEqual(fact["text"], "Test fact")
        self.assertEqual(fact["source"], "user")
        self.assertEqual(fact["confidence"], 0.9)
        self.assertIn("created_at", fact)
        self.assertEqual(fact["access_count"], 0)

    def test_add_fact_with_defaults(self):
        """Test adding a fact with default parameters."""
        result = self.manager.add_fact("Default fact")

        self.assertTrue(result)

        fact = self.manager.knowledge_base["facts"][0]
        self.assertEqual(fact["source"], "user")
        self.assertEqual(fact["confidence"], 1.0)

    def test_get_facts(self):
        """Test getting facts from the knowledge base."""
        # Add some test facts
        self.manager.add_fact("Fact 1", "user", 0.8)
        self.manager.add_fact("Fact 2", "inference", 0.6)
        self.manager.add_fact("Fact 3", "user", 0.9)

        # Get all facts
        all_facts = self.manager.get_facts()
        self.assertEqual(len(all_facts), 3)

        # Get facts by source
        user_facts = self.manager.get_facts(filter_source="user")
        self.assertEqual(len(user_facts), 2)

        # Get facts by confidence
        high_confidence_facts = self.manager.get_facts(min_confidence=0.7)
        self.assertEqual(len(high_confidence_facts), 2)

        # Get facts by both source and confidence
        filtered_facts = self.manager.get_facts(
            filter_source="user", min_confidence=0.85
        )
        self.assertEqual(len(filtered_facts), 1)
        self.assertEqual(filtered_facts[0]["text"], "Fact 3")

    def test_get_facts_updates_access_metadata(self):
        """Test that getting facts updates access metadata."""
        self.manager.add_fact("Test fact", "user")

        # Get facts should update access metadata
        facts = self.manager.get_facts()

        # Check that access metadata was updated
        fact = self.manager.knowledge_base["facts"][0]
        self.assertIsNotNone(fact["last_accessed"])
        self.assertEqual(fact["access_count"], 1)

        # Get facts again
        facts = self.manager.get_facts()
        fact = self.manager.knowledge_base["facts"][0]
        self.assertEqual(fact["access_count"], 2)

    def test_set_preference(self):
        """Test setting user preferences."""
        result = self.manager.set_preference("ui", "theme", "dark")

        self.assertTrue(result)
        self.assertEqual(
            self.manager.knowledge_base["preferences"]["ui"]["theme"], "dark"
        )

    def test_set_preference_new_category(self):
        """Test setting preference in a new category."""
        result = self.manager.set_preference("notifications", "email", True)

        self.assertTrue(result)
        self.assertIn("notifications", self.manager.knowledge_base["preferences"])
        self.assertTrue(
            self.manager.knowledge_base["preferences"]["notifications"]["email"]
        )

    def test_get_preference(self):
        """Test getting user preferences."""
        # Set a preference first
        self.manager.set_preference("ui", "theme", "dark")

        # Get the preference
        theme = self.manager.get_preference("ui", "theme")
        self.assertEqual(theme, "dark")

        # Get non-existent preference with default
        font_size = self.manager.get_preference("ui", "font_size", 12)
        self.assertEqual(font_size, 12)

        # Get non-existent preference without default
        color = self.manager.get_preference("ui", "color")
        self.assertIsNone(color)

    def test_get_all_preferences(self):
        """Test getting all preferences."""
        # Set some preferences
        self.manager.set_preference("ui", "theme", "dark")
        self.manager.set_preference("ui", "font_size", 14)
        self.manager.set_preference("notifications", "email", True)

        # Get all preferences
        all_prefs = self.manager.get_all_preferences()
        self.assertIn("ui", all_prefs)
        self.assertIn("notifications", all_prefs)
        self.assertEqual(all_prefs["ui"]["theme"], "dark")

        # Get preferences by category
        ui_prefs = self.manager.get_all_preferences("ui")
        self.assertEqual(len(ui_prefs), 2)
        self.assertEqual(ui_prefs["theme"], "dark")
        self.assertEqual(ui_prefs["font_size"], 14)

    def test_add_entity(self):
        """Test adding an entity to the knowledge base."""
        properties = {"age": 30, "occupation": "developer"}
        result = self.manager.add_entity("John", "person", properties)

        self.assertTrue(result)
        self.assertIn("John", self.manager.knowledge_base["entities"])

        entity = self.manager.knowledge_base["entities"]["John"]
        self.assertEqual(entity["name"], "John")
        self.assertEqual(entity["type"], "person")
        self.assertEqual(entity["properties"]["age"], 30)
        self.assertIn("created_at", entity)
        self.assertIn("last_updated", entity)

    def test_add_entity_without_properties(self):
        """Test adding an entity without properties."""
        result = self.manager.add_entity("Company", "organization")

        self.assertTrue(result)

        entity = self.manager.knowledge_base["entities"]["Company"]
        self.assertEqual(entity["properties"], {})

    def test_get_entity(self):
        """Test getting an entity from the knowledge base."""
        # Add an entity first
        self.manager.add_entity("John", "person", {"age": 30})

        # Get the entity
        entity = self.manager.get_entity("John")
        self.assertIsNotNone(entity)
        self.assertEqual(entity["name"], "John")
        self.assertEqual(entity["type"], "person")

        # Get non-existent entity
        non_existent = self.manager.get_entity("NonExistent")
        self.assertIsNone(non_existent)

    def test_update_entity(self):
        """Test updating an entity's properties."""
        # Add an entity first
        self.manager.add_entity("John", "person", {"age": 30})

        # Update the entity
        result = self.manager.update_entity("John", {"age": 31, "city": "New York"})

        self.assertTrue(result)

        entity = self.manager.knowledge_base["entities"]["John"]
        self.assertEqual(entity["properties"]["age"], 31)
        self.assertEqual(entity["properties"]["city"], "New York")
        self.assertNotEqual(entity["created_at"], entity["last_updated"])

    def test_update_nonexistent_entity(self):
        """Test updating a non-existent entity."""
        result = self.manager.update_entity("NonExistent", {"age": 30})

        self.assertFalse(result)

    def test_add_relationship(self):
        """Test adding a relationship between entities."""
        properties = {"since": "2020", "type": "employment"}
        result = self.manager.add_relationship(
            "John", "works_at", "Company", properties
        )

        self.assertTrue(result)
        self.assertEqual(len(self.manager.knowledge_base["relationships"]), 1)

        relationship = self.manager.knowledge_base["relationships"][0]
        self.assertEqual(relationship["entity1"], "John")
        self.assertEqual(relationship["relation"], "works_at")
        self.assertEqual(relationship["entity2"], "Company")
        self.assertEqual(relationship["properties"]["since"], "2020")
        self.assertIn("created_at", relationship)

    def test_add_relationship_without_properties(self):
        """Test adding a relationship without properties."""
        result = self.manager.add_relationship("John", "knows", "Jane")

        self.assertTrue(result)

        relationship = self.manager.knowledge_base["relationships"][0]
        self.assertEqual(relationship["properties"], {})

    def test_get_relationships(self):
        """Test getting relationships from the knowledge base."""
        # Add some relationships
        self.manager.add_relationship("John", "works_at", "Company")
        self.manager.add_relationship("John", "knows", "Jane")
        self.manager.add_relationship("Jane", "works_at", "Company")

        # Get all relationships
        all_rels = self.manager.get_relationships()
        self.assertEqual(len(all_rels), 3)

        # Get relationships by entity
        john_rels = self.manager.get_relationships(entity="John")
        self.assertEqual(len(john_rels), 2)

        # Get relationships by relation type
        work_rels = self.manager.get_relationships(relation="works_at")
        self.assertEqual(len(work_rels), 2)

        # Get relationships by both entity and relation
        john_work_rels = self.manager.get_relationships(
            entity="John", relation="works_at"
        )
        self.assertEqual(len(john_work_rels), 1)
        self.assertEqual(john_work_rels[0]["entity2"], "Company")

    def test_clear_knowledge_base(self):
        """Test clearing the entire knowledge base."""
        # Add some data
        self.manager.add_fact("Test fact")
        self.manager.set_preference("ui", "theme", "dark")
        self.manager.add_entity("John", "person")
        self.manager.add_relationship("John", "knows", "Jane")

        # Clear the knowledge base
        result = self.manager.clear_knowledge_base()

        self.assertTrue(result)

        # Verify everything is cleared
        self.assertEqual(self.manager.knowledge_base["facts"], [])
        self.assertEqual(self.manager.knowledge_base["preferences"], {})
        self.assertEqual(self.manager.knowledge_base["entities"], {})
        self.assertEqual(self.manager.knowledge_base["relationships"], [])


class TestAgentFactManagerIntegration(unittest.TestCase):
    """Integration tests for AgentFactManager."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after integration tests."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_knowledge_manager_full_workflow(self):
        """Test a complete workflow with the knowledge manager."""
        manager = AgentFactManager(
            user_id="integration_test_user",
            storage_dir=self.temp_dir,
            lightrag_url="http://localhost:8020",
            lightrag_memory_url="http://localhost:8021",
        )

        # Add facts
        manager.add_fact("User likes programming", "user", 0.9)
        manager.add_fact("User works remotely", "inference", 0.7)

        # Set preferences
        manager.set_preference("ui", "theme", "dark")
        manager.set_preference("notifications", "email", True)

        # Add entities
        manager.add_entity("User", "person", {"name": "John", "age": 30})
        manager.add_entity(
            "Company", "organization", {"name": "TechCorp", "industry": "software"}
        )

        # Add relationships
        manager.add_relationship(
            "User", "works_at", "Company", {"position": "developer", "since": "2020"}
        )

        # Verify data integrity
        facts = manager.get_facts()
        self.assertEqual(len(facts), 2)

        prefs = manager.get_all_preferences()
        self.assertEqual(len(prefs), 2)
        self.assertEqual(prefs["ui"]["theme"], "dark")

        entities = manager.knowledge_base["entities"]
        self.assertEqual(len(entities), 2)
        self.assertIn("User", entities)
        self.assertIn("Company", entities)

        relationships = manager.get_relationships()
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0]["entity1"], "User")
        self.assertEqual(relationships[0]["relation"], "works_at")
        self.assertEqual(relationships[0]["entity2"], "Company")

        # Test persistence by creating a new manager instance
        manager2 = AgentFactManager(
            user_id="integration_test_user", storage_dir=self.temp_dir
        )

        # Data should be loaded from file
        self.assertEqual(len(manager2.knowledge_base["facts"]), 2)
        self.assertEqual(len(manager2.knowledge_base["entities"]), 2)
        self.assertEqual(len(manager2.knowledge_base["relationships"]), 1)


if __name__ == "__main__":
    unittest.main()
