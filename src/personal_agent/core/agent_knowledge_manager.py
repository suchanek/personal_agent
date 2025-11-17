"""
Agent Fact Manager for the Personal AI Agent.

This module manages USER FACTS and PREFERENCES about the agent's user.
It stores facts locally and optionally syncs them to the LightRAG Memory server (port 9622).

IMPORTANT: Despite the historical name, this manages FACTS (not documents).
For document ingestion, use KnowledgeTools with KnowledgeStorageManager.
"""

import asyncio
import datetime
import json
import os
from typing import Dict, List, Optional, Tuple, Union, Any

import aiohttp
from textwrap import dedent

# Configure logging
import logging
logger = logging.getLogger(__name__)


class AgentFactManager:
    """
    Manages USER FACTS and PREFERENCES for the Personal AI Agent.

    This class stores facts locally in JSON format and optionally syncs them
    to the LightRAG Memory server (port 9622).

    IMPORTANT: This manager handles FACTS about the user, NOT document ingestion.
    For document/text/URL ingestion, use KnowledgeTools with KnowledgeStorageManager.

    Sync Target: LightRAG Memory Server (port 9622), not Knowledge Server (port 9621)
    """

    def __init__(self, user_id: str, storage_dir: str,
                 lightrag_url: Optional[str] = None,
                 lightrag_memory_url: Optional[str] = None):
        """Initialize the fact manager.
        
        Args:
            user_id: User identifier for knowledge operations
            storage_dir: Directory for storage files
            lightrag_url: Optional URL for LightRAG API
            lightrag_memory_url: Optional URL for LightRAG Memory API
        """
        self.user_id = user_id
        self.storage_dir = storage_dir
        self.lightrag_url = lightrag_url
        self.lightrag_memory_url = lightrag_memory_url
        self.knowledge_base_file = os.path.join(storage_dir, f"{user_id}_knowledge.json")
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict:
        """Load the knowledge base from file.
        
        Returns:
            Dict containing the knowledge base
        """
        try:
            if os.path.exists(self.knowledge_base_file):
                with open(self.knowledge_base_file, "r") as f:
                    return json.load(f)
            else:
                # Initialize with empty structure
                knowledge_base = {
                    "facts": [],
                    "preferences": {},
                    "entities": {},
                    "relationships": [],
                    "metadata": {
                        "version": "1.0",
                        "last_updated": None
                    }
                }
                # Save the initial structure
                self._save_knowledge_base(knowledge_base)
                return knowledge_base
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            # Return a default empty structure
            return {
                "facts": [],
                "preferences": {},
                "entities": {},
                "relationships": [],
                "metadata": {
                    "version": "1.0",
                    "last_updated": None
                }
            }
            
    def _save_knowledge_base(self, knowledge_base: Optional[Dict] = None) -> bool:
        """Save the knowledge base to file.
        
        Args:
            knowledge_base: Optional knowledge base to save (uses self.knowledge_base if None)
            
        Returns:
            True if save was successful
        """
        try:
            kb = knowledge_base if knowledge_base is not None else self.knowledge_base
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.knowledge_base_file), exist_ok=True)
            
            # Update metadata
            import datetime
            kb["metadata"]["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.knowledge_base_file, "w") as f:
                json.dump(kb, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
            return False
            
    def add_fact(self, fact: str, source: str = "user", confidence: float = 1.0) -> bool:
        """Add a fact to the knowledge base.
        
        Args:
            fact: The fact to add
            source: Source of the fact (user, inference, etc.)
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            True if fact was added successfully
        """
        try:
            # Create a fact object
            import datetime
            fact_obj = {
                "text": fact,
                "source": source,
                "confidence": confidence,
                "created_at": datetime.datetime.now().isoformat(),
                "last_accessed": None,
                "access_count": 0
            }
            
            # Add to knowledge base
            self.knowledge_base["facts"].append(fact_obj)
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error adding fact: {e}")
            return False
            
    def get_facts(self, filter_source: Optional[str] = None, min_confidence: float = 0.0) -> List[Dict]:
        """Get facts from the knowledge base with optional filtering.
        
        Args:
            filter_source: Optional source to filter by
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of fact objects
        """
        try:
            facts = self.knowledge_base["facts"]
            
            # Apply filters
            if filter_source:
                facts = [f for f in facts if f.get("source") == filter_source]
                
            facts = [f for f in facts if f.get("confidence", 0.0) >= min_confidence]
            
            # Update access metadata
            import datetime
            now = datetime.datetime.now().isoformat()
            
            for fact in facts:
                # Find the original fact in the knowledge base and update it
                for kb_fact in self.knowledge_base["facts"]:
                    if kb_fact.get("text") == fact.get("text"):
                        kb_fact["last_accessed"] = now
                        kb_fact["access_count"] = kb_fact.get("access_count", 0) + 1
            
            # Save the updated knowledge base
            self._save_knowledge_base()
            
            return facts
        except Exception as e:
            logger.error(f"Error getting facts: {e}")
            return []
            
    def set_preference(self, category: str, key: str, value: Any) -> bool:
        """Set a user preference.
        
        Args:
            category: Preference category (e.g., 'communication', 'interface')
            key: Preference key
            value: Preference value
            
        Returns:
            True if preference was set successfully
        """
        try:
            # Initialize category if it doesn't exist
            if category not in self.knowledge_base["preferences"]:
                self.knowledge_base["preferences"][category] = {}
                
            # Set preference
            self.knowledge_base["preferences"][category][key] = value
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error setting preference: {e}")
            return False
            
    def get_preference(self, category: str, key: str, default: Any = None) -> Any:
        """Get a user preference.
        
        Args:
            category: Preference category
            key: Preference key
            default: Default value if preference doesn't exist
            
        Returns:
            Preference value or default
        """
        try:
            return self.knowledge_base["preferences"].get(category, {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return default
            
    def get_all_preferences(self, category: Optional[str] = None) -> Dict:
        """Get all preferences, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Dictionary of preferences
        """
        try:
            if category:
                return self.knowledge_base["preferences"].get(category, {})
            else:
                return self.knowledge_base["preferences"]
        except Exception as e:
            logger.error(f"Error getting all preferences: {e}")
            return {}
            
    def add_entity(self, entity_name: str, entity_type: str, properties: Dict = None) -> bool:
        """Add an entity to the knowledge base.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of the entity (person, place, thing, etc.)
            properties: Optional properties of the entity
            
        Returns:
            True if entity was added successfully
        """
        try:
            # Create entity object
            import datetime
            entity_obj = {
                "name": entity_name,
                "type": entity_type,
                "properties": properties or {},
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Add to knowledge base
            self.knowledge_base["entities"][entity_name] = entity_obj
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            return False
            
    def get_entity(self, entity_name: str) -> Optional[Dict]:
        """Get an entity from the knowledge base.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Entity object or None if not found
        """
        try:
            return self.knowledge_base["entities"].get(entity_name)
        except Exception as e:
            logger.error(f"Error getting entity: {e}")
            return None
            
    def update_entity(self, entity_name: str, properties: Dict) -> bool:
        """Update an entity's properties.
        
        Args:
            entity_name: Name of the entity
            properties: Properties to update
            
        Returns:
            True if entity was updated successfully
        """
        try:
            # Check if entity exists
            if entity_name not in self.knowledge_base["entities"]:
                logger.warning(f"Entity {entity_name} not found")
                return False
                
            # Update properties
            entity = self.knowledge_base["entities"][entity_name]
            entity["properties"].update(properties)
            
            # Update the last_updated timestamp
            import datetime
            entity["last_updated"] = datetime.datetime.now().isoformat()
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            return False
            
    def add_relationship(self, entity1: str, relation: str, entity2: str, properties: Dict = None) -> bool:
        """Add a relationship between entities.
        
        Args:
            entity1: First entity name
            relation: Relationship type
            entity2: Second entity name
            properties: Optional properties of the relationship
            
        Returns:
            True if relationship was added successfully
        """
        try:
            # Create relationship object
            import datetime
            rel_obj = {
                "entity1": entity1,
                "relation": relation,
                "entity2": entity2,
                "properties": properties or {},
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Add to knowledge base
            self.knowledge_base["relationships"].append(rel_obj)
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return False
            
    def get_relationships(self, entity: Optional[str] = None, relation: Optional[str] = None) -> List[Dict]:
        """Get relationships, optionally filtered by entity or relation type.
        
        Args:
            entity: Optional entity to filter by (either entity1 or entity2)
            relation: Optional relation type to filter by
            
        Returns:
            List of relationship objects
        """
        try:
            relationships = self.knowledge_base["relationships"]
            
            # Apply filters
            if entity:
                relationships = [
                    r for r in relationships 
                    if r.get("entity1") == entity or r.get("entity2") == entity
                ]
                
            if relation:
                relationships = [r for r in relationships if r.get("relation") == relation]
                
            return relationships
        except Exception as e:
            logger.error(f"Error getting relationships: {e}")
            return []
            
    def clear_knowledge_base(self) -> bool:
        """Clear the entire knowledge base.
        
        Returns:
            True if knowledge base was cleared successfully
        """
        try:
            # Reset to empty structure
            self.knowledge_base = {
                "facts": [],
                "preferences": {},
                "entities": {},
                "relationships": [],
                "metadata": {
                    "version": "1.0",
                    "last_updated": None
                }
            }
            
            # Save knowledge base
            return self._save_knowledge_base()
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return False
            
    async def sync_facts_to_memory(self) -> str:
        """Synchronize local facts with the LightRAG Memory server (port 9622).

        This method syncs entities and relationships from the local fact store
        to the LightRAG Memory graph database.

        Note: Renamed from sync_with_graph() for clarity about destination.

        :return: Status message with sync results
        """
        if not self.lightrag_memory_url:
            return "Graph sync not available: LightRAG memory URL not configured"
            
        try:
            results = []
            
            # 1. Sync entities
            for entity_name, entity in self.knowledge_base["entities"].items():
                try:
                    # Check if entity exists in graph
                    entity_exists = await self._check_entity_exists(entity_name)
                    
                    if not entity_exists:
                        # Create entity in graph
                        success = await self._create_graph_entity(
                            entity_name, entity["type"], entity["properties"]
                        )
                        
                        if success:
                            results.append(f"Created entity: {entity_name}")
                        else:
                            results.append(f"Failed to create entity: {entity_name}")
                    else:
                        # Update entity in graph
                        success = await self._update_graph_entity(
                            entity_name, entity["properties"]
                        )
                        
                        if success:
                            results.append(f"Updated entity: {entity_name}")
                        else:
                            results.append(f"Failed to update entity: {entity_name}")
                except Exception as e:
                    logger.error(f"Error syncing entity {entity_name}: {e}")
                    results.append(f"Error syncing entity {entity_name}: {str(e)}")
                    
            # 2. Sync relationships
            for rel in self.knowledge_base["relationships"]:
                try:
                    # Create relationship in graph
                    success = await self._create_graph_relationship(
                        rel["entity1"], rel["relation"], rel["entity2"], rel["properties"]
                    )
                    
                    if success:
                        results.append(f"Created relationship: {rel['entity1']} {rel['relation']} {rel['entity2']}")
                    else:
                        results.append(f"Failed to create relationship: {rel['entity1']} {rel['relation']} {rel['entity2']}")
                except Exception as e:
                    logger.error(f"Error syncing relationship: {e}")
                    results.append(f"Error syncing relationship: {str(e)}")
                    
            # Return combined results
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error syncing with graph: {e}")
            return f"Error syncing with graph: {str(e)}"
            
    async def _check_entity_exists(self, entity_name: str) -> bool:
        """Check if entity exists in the graph.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            True if entity exists
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/entity/exists"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"entity_name": entity_name}, timeout=10) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("exists", False)
                    else:
                        logger.warning(f"Failed to check entity existence: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Error checking entity existence: {e}")
            return False
            
    async def _create_graph_entity(self, entity_name: str, entity_type: str, properties: Dict) -> bool:
        """Create an entity in the graph.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of the entity
            properties: Properties of the entity
            
        Returns:
            True if entity was created successfully
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/entity/create"
            
            payload = {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "properties": properties
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status in [200, 201]:
                        logger.info(f"Created entity in graph: {entity_name}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.warning(f"Failed to create entity in graph: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error creating graph entity: {e}")
            return False
            
    async def _update_graph_entity(self, entity_name: str, properties: Dict) -> bool:
        """Update an entity in the graph.
        
        Args:
            entity_name: Name of the entity
            properties: Properties to update
            
        Returns:
            True if entity was updated successfully
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/entity/update"
            
            payload = {
                "entity_name": entity_name,
                "properties": properties
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        logger.info(f"Updated entity in graph: {entity_name}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.warning(f"Failed to update entity in graph: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error updating graph entity: {e}")
            return False
            
    async def _create_graph_relationship(self, entity1: str, relation: str, entity2: str, properties: Dict) -> bool:
        """Create a relationship in the graph.
        
        Args:
            entity1: First entity name
            relation: Relationship type
            entity2: Second entity name
            properties: Properties of the relationship
            
        Returns:
            True if relationship was created successfully
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/relationship/create"
            
            payload = {
                "entity1": entity1,
                "relation": relation,
                "entity2": entity2,
                "properties": properties
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status in [200, 201]:
                        logger.info(f"Created relationship in graph: {entity1} {relation} {entity2}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.warning(f"Failed to create relationship in graph: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error creating graph relationship: {e}")
            return False
            
    async def query_graph(self, query: str) -> Dict:
        """Query the graph database.

        :param query: Cypher query
        :return: Query results
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/query"

            payload = {
                "query": query
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        logger.warning(f"Failed to query graph: {error_text}")
                        return {"error": error_text}
        except Exception as e:
            logger.error(f"Error querying graph: {e}")
            return {"error": str(e)}

    # Backward compatibility alias
    async def sync_with_graph(self) -> str:
        """
        Deprecated: Use sync_facts_to_memory() instead.

        This method is maintained for backward compatibility.
        """
        return await self.sync_facts_to_memory()


# Backward compatibility alias
AgentKnowledgeManager = AgentFactManager