"""
Unit tests for AgentModelManager.

This module tests the model creation and configuration functionality
extracted from the AgnoPersonalAgent class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.personal_agent.core.agent_model_manager import AgentModelManager


class TestAgentModelManager:
    """Test cases for AgentModelManager."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.model_provider = "ollama"
        self.model_name = "llama2"
        self.ollama_base_url = "http://localhost:11434"
        self.seed = 42
        
        self.manager = AgentModelManager(
            model_provider=self.model_provider,
            model_name=self.model_name,
            ollama_base_url=self.ollama_base_url,
            seed=self.seed
        )
    
    def test_init(self):
        """Test AgentModelManager initialization."""
        assert self.manager.model_provider == self.model_provider
        assert self.manager.model_name == self.model_name
        assert self.manager.ollama_base_url == self.ollama_base_url
        assert self.manager.seed == self.seed
    
    def test_init_without_seed(self):
        """Test AgentModelManager initialization without seed."""
        manager = AgentModelManager(
            model_provider="ollama",
            model_name="llama2",
            ollama_base_url="http://localhost:11434"
        )
        assert manager.seed is None
    
    @patch('src.personal_agent.core.agent_model_manager.get_model_context_size_sync')
    @patch('src.personal_agent.core.agent_model_manager.Ollama')
    def test_create_model_ollama(self, mock_ollama, mock_get_context_size):
        """Test creating an Ollama model."""
        # Mock the context size detection
        mock_get_context_size.return_value = (4096, "api_detection")
        mock_model_instance = Mock()
        mock_ollama.return_value = mock_model_instance
        
        result = self.manager.create_model()
        
        # Verify context size was called correctly
        mock_get_context_size.assert_called_once_with(
            self.model_name, self.ollama_base_url
        )
        
        # Verify Ollama was instantiated correctly
        mock_ollama.assert_called_once_with(
            id=self.model_name,
            host=self.ollama_base_url,
            options={
                "num_ctx": 4096,
                "temperature": 0.7,
                "num_predict": -1,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "seed": self.seed,
            }
        )
        
        assert result == mock_model_instance
    
    @patch('src.personal_agent.core.agent_model_manager.get_model_context_size_sync')
    @patch('src.personal_agent.core.agent_model_manager.Ollama')
    def test_create_model_ollama_without_seed(self, mock_ollama, mock_get_context_size):
        """Test creating an Ollama model without seed."""
        # Create manager without seed
        manager = AgentModelManager(
            model_provider="ollama",
            model_name="llama2",
            ollama_base_url="http://localhost:11434"
        )
        
        # Mock the context size detection
        mock_get_context_size.return_value = (8192, "model_info")
        mock_model_instance = Mock()
        mock_ollama.return_value = mock_model_instance
        
        result = manager.create_model()
        
        # Verify Ollama was instantiated with None seed
        mock_ollama.assert_called_once_with(
            id="llama2",
            host="http://localhost:11434",
            options={
                "num_ctx": 8192,
                "temperature": 0.7,
                "num_predict": -1,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "seed": None,
            }
        )
        
        assert result == mock_model_instance
    
    @patch('src.personal_agent.core.agent_model_manager.OpenAIChat')
    def test_create_model_openai(self, mock_openai):
        """Test creating an OpenAI model."""
        # Create manager for OpenAI
        manager = AgentModelManager(
            model_provider="openai",
            model_name="gpt-4",
            ollama_base_url="http://localhost:11434"
        )
        
        mock_model_instance = Mock()
        mock_openai.return_value = mock_model_instance
        
        result = manager.create_model()
        
        # Verify OpenAIChat was instantiated correctly
        mock_openai.assert_called_once_with(id="gpt-4")
        
        assert result == mock_model_instance
    
    def test_create_model_unsupported_provider(self):
        """Test creating a model with unsupported provider."""
        # Create manager with unsupported provider
        manager = AgentModelManager(
            model_provider="unsupported",
            model_name="some-model",
            ollama_base_url="http://localhost:11434"
        )
        
        with pytest.raises(ValueError, match="Unsupported model provider: unsupported"):
            manager.create_model()
    
    @patch('src.personal_agent.core.agent_model_manager.get_model_context_size_sync')
    @patch('src.personal_agent.core.agent_model_manager.Ollama')
    def test_create_model_context_size_detection_methods(self, mock_ollama, mock_get_context_size):
        """Test different context size detection methods."""
        test_cases = [
            (2048, "api_detection"),
            (4096, "model_info"),
            (8192, "default_fallback"),
        ]
        
        for context_size, detection_method in test_cases:
            mock_get_context_size.return_value = (context_size, detection_method)
            mock_model_instance = Mock()
            mock_ollama.return_value = mock_model_instance
            
            result = self.manager.create_model()
            
            # Verify the context size was used correctly
            call_args = mock_ollama.call_args
            assert call_args[1]["options"]["num_ctx"] == context_size
            
            # Reset mocks for next iteration
            mock_ollama.reset_mock()
            mock_get_context_size.reset_mock()
    
    @patch('src.personal_agent.core.agent_model_manager.get_model_context_size_sync')
    def test_create_model_context_size_exception(self, mock_get_context_size):
        """Test handling of context size detection exceptions."""
        # Mock an exception in context size detection
        mock_get_context_size.side_effect = Exception("Context size detection failed")
        
        with pytest.raises(Exception, match="Context size detection failed"):
            self.manager.create_model()
    
    def test_model_provider_case_sensitivity(self):
        """Test that model provider comparison is case sensitive."""
        # Test with different cases
        test_cases = [
            ("OLLAMA", ValueError),
            ("Ollama", ValueError),
            ("OPENAI", ValueError),
            ("OpenAI", ValueError),
            ("ollama", None),  # Should work
            ("openai", None),  # Should work
        ]
        
        for provider, expected_exception in test_cases:
            manager = AgentModelManager(
                model_provider=provider,
                model_name="test-model",
                ollama_base_url="http://localhost:11434"
            )
            
            if expected_exception:
                with pytest.raises(expected_exception):
                    manager.create_model()
            else:
                # These should not raise exceptions (though they might fail for other reasons)
                # We're just testing that the provider check passes
                try:
                    with patch('src.personal_agent.core.agent_model_manager.get_model_context_size_sync') as mock_context:
                        mock_context.return_value = (4096, "test")
                        with patch('src.personal_agent.core.agent_model_manager.Ollama') as mock_ollama:
                            mock_ollama.return_value = Mock()
                            manager.create_model()
                except Exception as e:
                    # If it's not a ValueError about unsupported provider, that's fine
                    if "Unsupported model provider" in str(e):
                        pytest.fail(f"Provider {provider} should be supported")


class TestAgentModelManagerIntegration:
    """Integration tests for AgentModelManager."""
    
    def test_model_manager_with_real_parameters(self):
        """Test model manager with realistic parameters."""
        manager = AgentModelManager(
            model_provider="ollama",
            model_name="llama3.2:3b",
            ollama_base_url="http://localhost:11434",
            seed=12345
        )
        
        assert manager.model_provider == "ollama"
        assert manager.model_name == "llama3.2:3b"
        assert manager.ollama_base_url == "http://localhost:11434"
        assert manager.seed == 12345
    
    def test_model_manager_parameter_validation(self):
        """Test parameter validation during initialization."""
        # Test with None values
        manager = AgentModelManager(
            model_provider="ollama",
            model_name="llama2",
            ollama_base_url="http://localhost:11434",
            seed=None
        )
        
        assert manager.seed is None
        
        # Test with empty strings (should still work)
        manager = AgentModelManager(
            model_provider="ollama",
            model_name="",
            ollama_base_url="",
            seed=0
        )
        
        assert manager.model_name == ""
        assert manager.ollama_base_url == ""
        assert manager.seed == 0


if __name__ == "__main__":
    pytest.main([__file__])
