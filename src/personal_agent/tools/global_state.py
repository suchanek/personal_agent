"""
Global State Manager for Personal Agent REST API

This module provides a thread-safe global state manager that allows sharing
of agent/team instances and helper objects between the Streamlit main thread
and the REST API server thread.

Since Streamlit's session state is thread-local and cannot be shared across
threads, this global state manager provides a way to share initialized
agent/team systems with the REST API server.
"""

import threading
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


class GlobalStateManager:
    """Thread-safe global state manager for sharing agent/team instances."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {}
        
    def set(self, key: str, value: Any) -> None:
        """Set a value in the global state."""
        with self._lock:
            self._state[key] = value
            logger.info(f"Global state updated: {key} = {value is not None}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the global state."""
        with self._lock:
            return self._state.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the global state."""
        with self._lock:
            return key in self._state
    
    def remove(self, key: str) -> None:
        """Remove a key from the global state."""
        with self._lock:
            if key in self._state:
                del self._state[key]
                logger.info(f"Global state removed: {key}")
    
    def clear(self) -> None:
        """Clear all global state."""
        with self._lock:
            self._state.clear()
            logger.info("Global state cleared")
    
    def get_status(self) -> Dict[str, bool]:
        """Get the status of all systems."""
        with self._lock:
            return {
                "agent_available": self._state.get("agent") is not None,
                "team_available": self._state.get("team") is not None,
                "memory_helper_available": self._state.get("memory_helper") is not None,
                "knowledge_helper_available": self._state.get("knowledge_helper") is not None,
                "agent_mode": self._state.get("agent_mode", "single")
            }


# Global instance
_global_state = GlobalStateManager()


def get_global_state() -> GlobalStateManager:
    """Get the global state manager instance."""
    return _global_state


def update_global_state_from_streamlit(session_state) -> None:
    """Update global state with current Streamlit session state."""
    global_state = get_global_state()
    
    # Update all relevant state
    global_state.set("agent_mode", session_state.get("agent_mode", "single"))
    global_state.set("agent", session_state.get("agent"))
    global_state.set("team", session_state.get("team"))
    global_state.set("memory_helper", session_state.get("memory_helper"))
    global_state.set("knowledge_helper", session_state.get("knowledge_helper"))
    
    logger.info("Global state updated from Streamlit session")
