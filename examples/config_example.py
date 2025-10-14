"""
Example: Using PersonalAgentConfig for centralized configuration management
==========================================================================

This example demonstrates how to use the new PersonalAgentConfig class
to manage application configuration in a thread-safe, centralized way.
"""

from personal_agent.config.runtime_config import get_config


def on_provider_change(key, old_value, new_value):
    """Callback function that gets notified when provider changes."""
    print(f"🔔 Configuration changed: {key} = {old_value} -> {new_value}")


def main():
    # Get the global configuration instance
    config = get_config()

    print("=" * 70)
    print("PersonalAgentConfig Example")
    print("=" * 70)

    # Display initial configuration
    print("\n📋 Initial Configuration:")
    print(f"  User ID: {config.user_id}")
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.model}")
    print(f"  Agent Mode: {config.agent_mode}")
    print(f"  Debug Mode: {config.debug_mode}")
    print(f"  Use Remote: {config.use_remote}")
    print(f"  Effective URL: {config.get_effective_base_url()}")

    # Register a callback to be notified of changes
    print("\n📢 Registering change callback...")
    config.register_callback(on_provider_change)

    # Example 1: Switch to LM Studio
    print("\n" + "=" * 70)
    print("Example 1: Switching to LM Studio")
    print("=" * 70)
    config.set_provider("lm-studio", auto_set_model=True)
    print(f"  New Provider: {config.provider}")
    print(f"  New Model: {config.model}")
    print(f"  Effective URL: {config.get_effective_base_url()}")

    # Example 2: Switch to OpenAI
    print("\n" + "=" * 70)
    print("Example 2: Switching to OpenAI")
    print("=" * 70)
    config.set_provider("openai", auto_set_model=True)
    print(f"  New Provider: {config.provider}")
    print(f"  New Model: {config.model}")
    print(f"  Effective URL: {config.get_effective_base_url()}")

    # Example 3: Switch back to Ollama with custom model
    print("\n" + "=" * 70)
    print("Example 3: Switching to Ollama with custom model")
    print("=" * 70)
    config.set_provider("ollama", auto_set_model=False)
    config.set_model("llama3.1:8b")
    print(f"  New Provider: {config.provider}")
    print(f"  New Model: {config.model}")
    print(f"  Effective URL: {config.get_effective_base_url()}")

    # Example 4: Toggle remote endpoints
    print("\n" + "=" * 70)
    print("Example 4: Toggling remote endpoints")
    print("=" * 70)
    print(f"  Current URL (local): {config.get_effective_base_url()}")
    config.set_use_remote(True)
    print(f"  New URL (remote): {config.get_effective_base_url()}")
    config.set_use_remote(False)
    print(f"  Back to URL (local): {config.get_effective_base_url()}")

    # Example 5: Agent mode switching
    print("\n" + "=" * 70)
    print("Example 5: Agent mode switching")
    print("=" * 70)
    print(f"  Current mode: {config.agent_mode}")
    config.set_agent_mode("single")
    print(f"  New mode: {config.agent_mode}")
    config.set_agent_mode("team")
    print(f"  Back to: {config.agent_mode}")

    # Example 6: Custom configuration values
    print("\n" + "=" * 70)
    print("Example 6: Custom configuration values")
    print("=" * 70)
    config.set("custom_key", "custom_value")
    config.set("api_timeout", 30)
    print(f"  Custom key: {config.get('custom_key')}")
    print(f"  API timeout: {config.get('api_timeout')}")
    print(f"  Non-existent key: {config.get('nonexistent', 'default')}")

    # Example 7: Configuration snapshot
    print("\n" + "=" * 70)
    print("Example 7: Configuration snapshot")
    print("=" * 70)
    snapshot = config.snapshot()
    print(f"  Snapshot provider: {snapshot.provider}")
    print(f"  Snapshot model: {snapshot.model}")
    print(f"  Snapshot user_id: {snapshot.user_id}")

    # Example 8: Export to dictionary
    print("\n" + "=" * 70)
    print("Example 8: Export configuration to dictionary")
    print("=" * 70)
    config_dict = config.to_dict()
    for key, value in sorted(config_dict.items()):
        if key != "extra":  # Skip extra dict for brevity
            print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
