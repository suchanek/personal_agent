"""
Personal Agent Runtime Configuration Manager
============================================

This module provides a centralized, thread-safe configuration management system
for the Personal Agent application. It replaces the scattered use of environment
variables with a proper singleton configuration object.

The PersonalAgentConfig class manages all runtime state including:
- Current user ID
- LLM provider and model
- Service URLs (Ollama, LM Studio, LightRAG)
- Feature flags and debug settings
- Application mode (single/team)

Key Features:
- Thread-safe singleton pattern
- Configuration change callbacks
- Environment variable fallbacks
- Validation and type safety
- Dynamic provider switching
- Immutable configuration snapshots

Usage:
    from personal_agent.config.runtime_config import get_config

    config = get_config()
    config.set_provider("lm-studio")
    config.set_model("qwen3-4b-instruct-2507-mlx")

    # Access configuration
    provider = config.provider
    model = config.model
    user_id = config.user_id
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# Provider-specific default models
PROVIDER_DEFAULT_MODELS = {
    "ollama": "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K",
    "lm-studio": "qwen3-4b-instruct-2507-mlx",
    "openai": "gpt-4o",
}


@dataclass
class ConfigSnapshot:
    """Immutable snapshot of configuration state.

    This allows components to safely cache configuration without
    worrying about concurrent modifications.
    """

    user_id: str
    provider: str
    model: str
    ollama_url: str
    remote_ollama_url: str
    lmstudio_url: str
    remote_lmstudio_url: str
    openai_url: str
    lightrag_url: str
    lightrag_memory_url: str
    agent_mode: str
    debug_mode: bool
    use_remote: bool
    use_mcp: bool
    enable_memory: bool
    seed: Optional[int]
    home_dir: str
    instruction_level: str
    user_storage_dir: str
    user_knowledge_dir: str
    user_data_dir: str
    agno_storage_dir: str
    agno_knowledge_dir: str
    lightrag_storage_dir: str
    lightrag_inputs_dir: str
    lightrag_memory_storage_dir: str
    lightrag_memory_inputs_dir: str
    persag_root: str
    storage_backend: str
    persag_home: str
    lightrag_port: str
    lightrag_memory_port: str
    root_dir: str
    repo_dir: str
    extra: Dict[str, Any] = field(default_factory=dict)


class PersonalAgentConfig:
    """Thread-safe singleton configuration manager for Personal Agent.

    This class provides centralized management of all application configuration,
    replacing the scattered use of environment variables and module-level globals.

    Features:
    - Thread-safe operations with locking
    - Change notification callbacks
    - Validation and type safety
    - Environment variable fallbacks
    - Provider-specific defaults
    - Configuration snapshots

    Example:
        config = PersonalAgentConfig.get_instance()
        config.set_provider("lm-studio")
        config.register_callback(on_config_change)
    """

    _instance: Optional["PersonalAgentConfig"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize configuration from environment variables.

        Note: Use get_instance() instead of calling this directly.
        """
        self._config_lock = threading.RLock()
        self._callbacks: List[Callable[[str, Any, Any], None]] = []

        # Load initial configuration from environment variables
        with self._config_lock:
            # Use the user_id_mgr to get the current user (reads from ~/.persag/env.userid)
            try:
                from personal_agent.config.user_id_mgr import get_userid

                self._user_id = get_userid()
            except ImportError:
                self._user_id = os.getenv("USER_ID", "default_user")

            self._provider = os.getenv("PROVIDER", "ollama")
            self._model = os.getenv(
                "LLM_MODEL", self._get_default_model(self._provider)
            )

            # Service URLs
            self._ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            self._remote_ollama_url = os.getenv(
                "REMOTE_OLLAMA_URL", "http://100.100.248.61:11434"
            )
            self._lmstudio_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234")
            self._remote_lmstudio_url = os.getenv(
                "REMOTE_LMSTUDIO_URL", "http://100.100.248.61:1234"
            )
            self._openai_url = "https://api.openai.com/v1"
            self._lightrag_url = os.getenv("LIGHTRAG_URL", "http://localhost:9621")
            self._lightrag_memory_url = os.getenv(
                "LIGHTRAG_MEMORY_URL", "http://localhost:9622"
            )

            # Application settings
            self._agent_mode = "team"  # "single" or "team"
            self._debug_mode = os.getenv("DEBUG", "false").lower() in (
                "true",
                "1",
                "yes",
            )
            self._use_remote = False
            self._use_mcp = os.getenv("USE_MCP", "true").lower() in (
                "true",
                "1",
                "yes",
            )
            self._enable_memory = os.getenv("ENABLE_MEMORY", "true").lower() in (
                "true",
                "1",
                "yes",
            )
            seed_env = os.getenv("LLM_SEED")
            self._seed = int(seed_env) if seed_env and seed_env.isdigit() else None
            self._instruction_level = os.getenv("INSTRUCTION_LEVEL", "CONCISE")

            # Home directory for shell tools
            self._home_dir = os.path.expanduser("~")

            # Path configurations
            self._persag_root = os.getenv(
                "PERSAG_ROOT", "/Users/Shared/personal_agent_data"
            )
            self._storage_backend = os.getenv("STORAGE_BACKEND", "agno")
            self._persag_home = os.getenv("PERSAG_HOME", str(Path.home() / ".persag"))

            # LightRAG server port configurations
            self._lightrag_port = os.getenv("LIGHTRAG_PORT", "9621")
            self._lightrag_memory_port = os.getenv("LIGHTRAG_MEMORY_PORT", "9622")

            # Directory configurations
            self._root_dir = os.getenv("ROOT_DIR", "/")
            self._repo_dir = os.getenv("REPO_DIR", "./repos")

            # Extra configuration storage
            self._extra: Dict[str, Any] = {}

        logger.info(
            "PersonalAgentConfig initialized: user=%s, provider=%s, model=%s",
            self._user_id,
            self._provider,
            self._model,
        )

    @classmethod
    def get_instance(cls) -> "PersonalAgentConfig":
        """Get the singleton configuration instance.

        Thread-safe singleton pattern ensures only one instance exists.

        Returns:
            PersonalAgentConfig: The singleton configuration instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (mainly for testing).

        WARNING: This should only be used in tests or during system restart.
        """
        with cls._lock:
            cls._instance = None

    def _get_default_model(self, provider: str) -> str:
        """Get the default model for a provider.

        :param provider: Provider name ('ollama', 'lm-studio', 'openai')
        :return: Default model name
        """
        return PROVIDER_DEFAULT_MODELS.get(provider, "qwen3:4b")

    def _notify_callbacks(self, key: str, old_value: Any, new_value: Any):
        """Notify all registered callbacks of a configuration change.

        :param key: Configuration key that changed
        :param old_value: Previous value
        :param new_value: New value
        """
        for callback in self._callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception:
                logger.exception("Error in config callback")

    def register_callback(self, callback: Callable[[str, Any, Any], None]):
        """Register a callback to be notified of configuration changes.

        :param callback: Function(key, old_value, new_value) to call on changes
        """
        with self._config_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, Any, Any], None]):
        """Unregister a configuration change callback.

        :param callback: Callback function to remove
        """
        with self._config_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    # ========== User ID ==========

    @property
    def user_id(self) -> str:
        """Get the current user ID."""
        with self._config_lock:
            return self._user_id

    def set_user_id(self, user_id: str, persist: bool = True):
        """Set the current user ID with proper persistence.

        This integrates with the existing user management system by:
        1. Setting the USER_ID environment variable
        2. Writing to ~/.persag/env.userid for persistence (if persist=True)
        3. Refreshing user-dependent settings (paths, etc.)

        :param user_id: New user ID
        :param persist: If True, write to ~/.persag/env.userid for persistence
        """
        with self._config_lock:
            old_value = self._user_id
            self._user_id = user_id
            os.environ["USER_ID"] = user_id
            logger.info("User ID changed: %s -> %s", old_value, user_id)

            # Persist to ~/.persag/env.userid if requested
            if persist:
                try:
                    from personal_agent.core.persag_manager import get_persag_manager

                    persag_manager = get_persag_manager()
                    success = persag_manager.set_userid(user_id)
                    if success:
                        logger.info("Persisted user ID to ~/.persag/env.userid")
                    else:
                        logger.warning(
                            "Could not persist user ID to ~/.persag/env.userid"
                        )
                except Exception:
                    logger.exception("Error persisting user ID")

                # CRITICAL: Refresh user-dependent settings AND update environment variables
                # This ensures Docker configurations receive the correct paths.
                try:
                    from personal_agent.config import refresh_user_dependent_settings

                    updated_settings = refresh_user_dependent_settings()
                    for key, value in updated_settings.items():
                        os.environ[key] = str(value)
                    logger.info(
                        "Refreshed and propagated user-dependent environment variables for Docker."
                    )
                except Exception:
                    logger.exception(
                        "Error refreshing user-dependent environment variables"
                    )

            self._notify_callbacks("user_id", old_value, user_id)

    # ========== Provider and Model ==========

    @property
    def provider(self) -> str:
        """Get the current LLM provider."""
        with self._config_lock:
            return self._provider

    def set_provider(self, provider: str, auto_set_model: bool = True):
        """Set the LLM provider and optionally update model to provider default.

        :param provider: Provider name ('ollama', 'lm-studio', 'openai')
        :param auto_set_model: If True, automatically set model to provider default
        """
        if provider not in PROVIDER_DEFAULT_MODELS:
            raise ValueError(
                f"Invalid provider: {provider}. Must be one of {list(PROVIDER_DEFAULT_MODELS.keys())}"
            )

        with self._config_lock:
            old_value = self._provider
            self._provider = provider
            os.environ["PROVIDER"] = provider
            logger.info("Provider changed: %s -> %s", old_value, provider)
            self._notify_callbacks("provider", old_value, provider)

            # Auto-set model to provider default if requested
            if auto_set_model:
                default_model = self._get_default_model(provider)
                self.set_model(default_model)

    @property
    def model(self) -> str:
        """Get the current model name."""
        with self._config_lock:
            return self._model

    def set_model(self, model: str):
        """Set the current model name.

        :param model: Model name
        """
        with self._config_lock:
            old_value = self._model
            self._model = model
            os.environ["LLM_MODEL"] = model
            logger.info("Model changed: %s -> %s", old_value, model)
            self._notify_callbacks("model", old_value, model)

    # ========== Service URLs ==========

    @property
    def ollama_url(self) -> str:
        """Get the Ollama server URL."""
        with self._config_lock:
            return self._ollama_url

    @property
    def remote_ollama_url(self) -> str:
        """Get the remote Ollama server URL."""
        with self._config_lock:
            return self._remote_ollama_url

    @property
    def lmstudio_url(self) -> str:
        """Get the LM Studio server URL."""
        with self._config_lock:
            return self._lmstudio_url

    @property
    def remote_lmstudio_url(self) -> str:
        """Get the remote LM Studio server URL."""
        with self._config_lock:
            return self._remote_lmstudio_url

    @property
    def openai_url(self) -> str:
        """Get the OpenAI API URL."""
        with self._config_lock:
            return self._openai_url

    @property
    def lightrag_url(self) -> str:
        """Get the LightRAG server URL."""
        with self._config_lock:
            return self._lightrag_url

    @property
    def lightrag_memory_url(self) -> str:
        """Get the LightRAG memory server URL."""
        with self._config_lock:
            return self._lightrag_memory_url

    def get_effective_base_url(self) -> str:
        """Get the effective base URL for the current provider and remote setting.

        Returns:
            str: The appropriate base URL for the current provider
        """
        with self._config_lock:
            if self._provider == "lm-studio":
                url = (
                    self._remote_lmstudio_url
                    if self._use_remote
                    else self._lmstudio_url
                )
                # Ensure LM Studio URL doesn't end with /v1 for consistency
                return url.rstrip("/v1").rstrip("/")
            elif self._provider == "openai":
                return self._openai_url
            else:  # ollama
                return self._remote_ollama_url if self._use_remote else self._ollama_url

    def get_effective_ollama_url(self) -> str:
        """Get the effective Ollama URL based on remote setting.

        This method is provider-agnostic and returns the appropriate URL
        for the current provider configuration. For backward compatibility,
        it's named for Ollama but works with all providers.

        Returns:
            str: The appropriate base URL for the current provider
        """
        return self.get_effective_base_url()

    # ========== User-Specific Paths ==========

    @property
    def persag_root(self) -> str:
        """Get the PERSAG_ROOT directory."""
        with self._config_lock:
            return self._persag_root

    @property
    def storage_backend(self) -> str:
        """Get the storage backend (typically 'agno')."""
        with self._config_lock:
            return self._storage_backend

    @property
    def user_storage_dir(self) -> str:
        """Get the user-specific storage directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}"
            )

    @property
    def user_knowledge_dir(self) -> str:
        """Get the user-specific knowledge directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/knowledge"
            )

    @property
    def user_data_dir(self) -> str:
        """Get the user-specific data directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/data"
            )

    @property
    def agno_storage_dir(self) -> str:
        """Get the AGNO storage directory (same as user_storage_dir)."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}"
            )

    @property
    def agno_knowledge_dir(self) -> str:
        """Get the AGNO knowledge directory (same as user_knowledge_dir)."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/knowledge"
            )

    @property
    def lightrag_storage_dir(self) -> str:
        """Get the LightRAG storage directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/rag_storage"
            )

    @property
    def lightrag_inputs_dir(self) -> str:
        """Get the LightRAG inputs directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/inputs"
            )

    @property
    def lightrag_memory_storage_dir(self) -> str:
        """Get the LightRAG memory storage directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/memory_rag_storage"
            )

    @property
    def lightrag_memory_inputs_dir(self) -> str:
        """Get the LightRAG memory inputs directory."""
        with self._config_lock:
            return os.path.expandvars(
                f"{self._persag_root}/{self._storage_backend}/{self._user_id}/memory_inputs"
            )

    @property
    def persag_home(self) -> str:
        """Get the PERSAG_HOME directory (typically ~/.persag)."""
        with self._config_lock:
            return self._persag_home

    @property
    def lightrag_port(self) -> str:
        """Get the LightRAG server port."""
        with self._config_lock:
            return self._lightrag_port

    @property
    def lightrag_memory_port(self) -> str:
        """Get the LightRAG memory server port."""
        with self._config_lock:
            return self._lightrag_memory_port

    @property
    def root_dir(self) -> str:
        """Get the root directory."""
        with self._config_lock:
            return self._root_dir

    @property
    def repo_dir(self) -> str:
        """Get the repository directory."""
        with self._config_lock:
            return self._repo_dir

    # ========== Application Settings ==========

    @property
    def agent_mode(self) -> str:
        """Get the agent mode ('single' or 'team')."""
        with self._config_lock:
            return self._agent_mode

    def set_agent_mode(self, mode: str):
        """Set the agent mode.

        :param mode: Agent mode ('single' or 'team')
        """
        if mode not in ("single", "team"):
            raise ValueError(f"Invalid agent mode: {mode}. Must be 'single' or 'team'")

        with self._config_lock:
            old_value = self._agent_mode
            self._agent_mode = mode
            logger.info("Agent mode changed: %s -> %s", old_value, mode)
            self._notify_callbacks("agent_mode", old_value, mode)

    @property
    def debug_mode(self) -> bool:
        """Get debug mode status."""
        with self._config_lock:
            return self._debug_mode

    def set_debug_mode(self, debug: bool):
        """Set debug mode.

        :param debug: Debug mode enabled/disabled
        """
        with self._config_lock:
            old_value = self._debug_mode
            self._debug_mode = debug
            os.environ["DEBUG"] = "true" if debug else "false"
            logger.info("Debug mode changed: %s -> %s", old_value, debug)
            self._notify_callbacks("debug_mode", old_value, debug)

    @property
    def use_remote(self) -> bool:
        """Get remote endpoint usage status."""
        with self._config_lock:
            return self._use_remote

    def set_use_remote(self, use_remote: bool):
        """Set whether to use remote endpoints.

        :param use_remote: Use remote endpoints if True, local if False
        """
        with self._config_lock:
            old_value = self._use_remote
            self._use_remote = use_remote
            logger.info(
                "Remote endpoint usage changed: %s -> %s", old_value, use_remote
            )
            self._notify_callbacks("use_remote", old_value, use_remote)

    @property
    def use_mcp(self) -> bool:
        """Get MCP usage status."""
        with self._config_lock:
            return self._use_mcp

    def set_use_mcp(self, use_mcp: bool):
        """Set MCP usage.

        :param use_mcp: Enable/disable MCP
        """
        with self._config_lock:
            old_value = self._use_mcp
            self._use_mcp = use_mcp
            os.environ["USE_MCP"] = "true" if use_mcp else "false"
            logger.info("MCP usage changed: %s -> %s", old_value, use_mcp)
            self._notify_callbacks("use_mcp", old_value, use_mcp)

    @property
    def seed(self) -> Optional[int]:
        """Get the model seed."""
        with self._config_lock:
            return self._seed

    @property
    def enable_memory(self) -> bool:
        """Get memory enable status."""
        with self._config_lock:
            return self._enable_memory

    def set_enable_memory(self, enable_memory: bool):
        """Set memory enable status.

        :param enable_memory: Enable/disable memory
        """
        with self._config_lock:
            old_value = self._enable_memory
            self._enable_memory = enable_memory
            os.environ["ENABLE_MEMORY"] = "true" if enable_memory else "false"
            logger.info("Memory enable changed: %s -> %s", old_value, enable_memory)
            self._notify_callbacks("enable_memory", old_value, enable_memory)

    @property
    def home_dir(self) -> str:
        """Get the home directory."""
        with self._config_lock:
            return self._home_dir

    @property
    def instruction_level(self) -> str:
        """Get the instruction level."""
        with self._config_lock:
            return self._instruction_level

    def set_instruction_level(self, level: str):
        """Set the instruction level.

        :param level: Instruction level (MINIMAL, CONCISE, STANDARD, EXPLICIT, EXPERIMENTAL)
        """
        valid_levels = ("MINIMAL", "CONCISE", "STANDARD", "EXPLICIT", "EXPERIMENTAL")
        if level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid instruction level: {level}. Must be one of {valid_levels}"
            )

        with self._config_lock:
            old_value = self._instruction_level
            self._instruction_level = level.upper()
            os.environ["INSTRUCTION_LEVEL"] = self._instruction_level
            logger.info(
                "Instruction level changed: %s -> %s",
                old_value,
                self._instruction_level,
            )
            self._notify_callbacks(
                "instruction_level", old_value, self._instruction_level
            )

    # ========== Extra Configuration ==========

    def get(self, key: str, default: Any = None) -> Any:
        """Get an extra configuration value.

        :param key: Configuration key
        :param default: Default value if key not found
        :return: Configuration value or default
        """
        with self._config_lock:
            return self._extra.get(key, default)

    def set(self, key: str, value: Any):
        """Set an extra configuration value.

        :param key: Configuration key
        :param value: Configuration value
        """
        with self._config_lock:
            old_value = self._extra.get(key)
            self._extra[key] = value
            logger.debug("Extra config changed: %s: %s -> %s", key, old_value, value)
            self._notify_callbacks(key, old_value, value)

    # ========== Configuration Snapshots ==========

    def snapshot(self) -> ConfigSnapshot:
        """Create an immutable snapshot of the current configuration.

        This allows components to cache configuration safely without
        worrying about concurrent modifications.

        Returns:
            ConfigSnapshot: Immutable configuration snapshot
        """
        with self._config_lock:
            return ConfigSnapshot(
                user_id=self._user_id,
                provider=self._provider,
                model=self._model,
                ollama_url=self._ollama_url,
                remote_ollama_url=self._remote_ollama_url,
                lmstudio_url=self._lmstudio_url,
                remote_lmstudio_url=self._remote_lmstudio_url,
                openai_url=self._openai_url,
                lightrag_url=self._lightrag_url,
                lightrag_memory_url=self._lightrag_memory_url,
                agent_mode=self._agent_mode,
                debug_mode=self._debug_mode,
                use_remote=self._use_remote,
                use_mcp=self._use_mcp,
                enable_memory=self._enable_memory,
                seed=self._seed,
                home_dir=self._home_dir,
                instruction_level=self._instruction_level,
                user_storage_dir=self.user_storage_dir,
                user_knowledge_dir=self.user_knowledge_dir,
                user_data_dir=self.user_data_dir,
                agno_storage_dir=self.agno_storage_dir,
                agno_knowledge_dir=self.agno_knowledge_dir,
                lightrag_storage_dir=self.lightrag_storage_dir,
                lightrag_inputs_dir=self.lightrag_inputs_dir,
                lightrag_memory_storage_dir=self.lightrag_memory_storage_dir,
                lightrag_memory_inputs_dir=self.lightrag_memory_inputs_dir,
                persag_root=self._persag_root,
                storage_backend=self._storage_backend,
                persag_home=self._persag_home,
                lightrag_port=self._lightrag_port,
                lightrag_memory_port=self._lightrag_memory_port,
                root_dir=self._root_dir,
                repo_dir=self._repo_dir,
                extra=self._extra.copy(),
            )

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary.

        Returns:
            dict: Configuration dictionary
        """
        snapshot = self.snapshot()
        return {
            "user_id": snapshot.user_id,
            "provider": snapshot.provider,
            "model": snapshot.model,
            "ollama_url": snapshot.ollama_url,
            "remote_ollama_url": snapshot.remote_ollama_url,
            "lmstudio_url": snapshot.lmstudio_url,
            "remote_lmstudio_url": snapshot.remote_lmstudio_url,
            "openai_url": snapshot.openai_url,
            "lightrag_url": snapshot.lightrag_url,
            "lightrag_memory_url": snapshot.lightrag_memory_url,
            "agent_mode": snapshot.agent_mode,
            "debug_mode": snapshot.debug_mode,
            "use_remote": snapshot.use_remote,
            "use_mcp": snapshot.use_mcp,
            "enable_memory": snapshot.enable_memory,
            "seed": snapshot.seed,
            "home_dir": snapshot.home_dir,
            "instruction_level": snapshot.instruction_level,
            "user_storage_dir": snapshot.user_storage_dir,
            "user_knowledge_dir": snapshot.user_knowledge_dir,
            "user_data_dir": snapshot.user_data_dir,
            "agno_storage_dir": snapshot.agno_storage_dir,
            "agno_knowledge_dir": snapshot.agno_knowledge_dir,
            "lightrag_storage_dir": snapshot.lightrag_storage_dir,
            "lightrag_inputs_dir": snapshot.lightrag_inputs_dir,
            "lightrag_memory_storage_dir": snapshot.lightrag_memory_storage_dir,
            "lightrag_memory_inputs_dir": snapshot.lightrag_memory_inputs_dir,
            "persag_root": snapshot.persag_root,
            "storage_backend": snapshot.storage_backend,
            "persag_home": snapshot.persag_home,
            "lightrag_port": snapshot.lightrag_port,
            "lightrag_memory_port": snapshot.lightrag_memory_port,
            "root_dir": snapshot.root_dir,
            "repo_dir": snapshot.repo_dir,
            "extra": snapshot.extra,
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"PersonalAgentConfig(user={self.user_id}, provider={self.provider}, model={self.model}, mode={self.agent_mode})"


# ========== Convenience Functions ==========


def get_config() -> PersonalAgentConfig:
    """Get the global configuration instance.

    This is the primary way to access configuration throughout the application.

    Returns:
        PersonalAgentConfig: The global configuration singleton

    Example:
        from personal_agent.config.runtime_config import get_config

        config = get_config()
        print(f"Current provider: {config.provider}")
        config.set_provider("lm-studio")
    """
    return PersonalAgentConfig.get_instance()


def reset_config():
    """Reset the configuration singleton (mainly for testing).

    WARNING: This should only be used in tests or during system restart.
    """
    PersonalAgentConfig.reset_instance()
