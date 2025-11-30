"""
LLM Provider Factory Module
Provides abstraction layer for different LLM and embedding providers.
"""
import os
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from dotenv import load_dotenv
from .utils import setup_logging

load_dotenv()

logger = setup_logging()


class LLMProviderFactory:
    """Factory for creating LLM instances from different providers."""
    
    @staticmethod
    def get_llm(provider_type: str, config: Dict[str, Any]) -> BaseChatModel:
        """
        Create an LLM instance based on provider type and configuration.
        
        Args:
            provider_type: Type of provider ('ollama', 'openrouter', 'openai', 'anthropic', 'azure-openai', 'google')
            config: Provider-specific configuration dictionary
            
        Returns:
            BaseChatModel: LangChain LLM instance
            
        Raises:
            ValueError: If provider type is not supported or configuration is invalid
        """
        provider_type = provider_type.lower()
        
        if provider_type == 'ollama':
            return LLMProviderFactory._create_ollama_llm(config)
        elif provider_type == 'openrouter':
            return LLMProviderFactory._create_openrouter_llm(config)
        elif provider_type == 'openai':
            return LLMProviderFactory._create_openai_llm(config)
        elif provider_type == 'anthropic':
            return LLMProviderFactory._create_anthropic_llm(config)
        elif provider_type == 'azure-openai':
            return LLMProviderFactory._create_azure_openai_llm(config)
        elif provider_type == 'google':
            return LLMProviderFactory._create_google_llm(config)
        else:
            raise ValueError(f"Unsupported LLM provider type: {provider_type}")
    
    @staticmethod
    def _create_ollama_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create Ollama LLM instance."""
        model = config.get('model', os.getenv('LLM_MODEL', 'mistral'))
        base_url = config.get('base_url', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
        temperature = config.get('temperature', 0)
        
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature
        )
    
    @staticmethod
    def _create_openrouter_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create OpenRouter LLM instance (uses OpenAI-compatible API)."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai is required for OpenRouter support. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        
        model = config.get('model', 'openai/gpt-4')
        base_url = config.get('base_url', 'https://openrouter.ai/api/v1')
        temperature = config.get('temperature', 0)
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": config.get('http_referer', ''),
                "X-Title": config.get('app_name', 'RAG System')
            }
        )
    
    @staticmethod
    def _create_openai_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create OpenAI LLM instance."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai is required for OpenAI support. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        model = config.get('model', 'gpt-4')
        temperature = config.get('temperature', 0)
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def _create_anthropic_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create Anthropic Claude LLM instance."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("langchain-anthropic is required for Anthropic support. Install it with: pip install langchain-anthropic")
        
        api_key = config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        model = config.get('model', 'claude-3-opus-20240229')
        temperature = config.get('temperature', 0)
        
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def _create_azure_openai_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create Azure OpenAI LLM instance."""
        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai is required for Azure OpenAI support. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('AZURE_OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Azure OpenAI API key is required")
        
        azure_endpoint = config.get('azure_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT')
        if not azure_endpoint:
            raise ValueError("Azure OpenAI endpoint is required")
        
        deployment_name = config.get('deployment_name') or config.get('model')
        if not deployment_name:
            raise ValueError("Azure OpenAI deployment name is required")
        
        api_version = config.get('api_version', '2024-02-15-preview')
        temperature = config.get('temperature', 0)
        
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_name,
            api_key=api_key,
            api_version=api_version,
            temperature=temperature
        )
    
    @staticmethod
    def _create_google_llm(config: Dict[str, Any]) -> BaseChatModel:
        """Create Google Gemini LLM instance."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError("langchain-google-genai is required for Google support. Install it with: pip install langchain-google-genai")
        
        api_key = config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key is required")
        
        model = config.get('model', 'gemini-pro')
        temperature = config.get('temperature', 0)
        
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature
        )


class EmbeddingProviderFactory:
    """Factory for creating embedding instances from different providers."""
    
    @staticmethod
    def get_embeddings(provider_type: str, config: Dict[str, Any]) -> Embeddings:
        """
        Create an embedding instance based on provider type and configuration.
        
        Args:
            provider_type: Type of provider ('ollama', 'openrouter', 'openai', 'azure-openai', 'google')
            config: Provider-specific configuration dictionary
            
        Returns:
            Embeddings: LangChain embeddings instance
            
        Raises:
            ValueError: If provider type is not supported or configuration is invalid
        """
        provider_type = provider_type.lower()
        
        if provider_type == 'ollama':
            return EmbeddingProviderFactory._create_ollama_embeddings(config)
        elif provider_type == 'openrouter':
            return EmbeddingProviderFactory._create_openrouter_embeddings(config)
        elif provider_type == 'openai':
            return EmbeddingProviderFactory._create_openai_embeddings(config)
        elif provider_type == 'azure-openai':
            return EmbeddingProviderFactory._create_azure_openai_embeddings(config)
        elif provider_type == 'google':
            return EmbeddingProviderFactory._create_google_embeddings(config)
        else:
            raise ValueError(f"Unsupported embedding provider type: {provider_type}")
    
    @staticmethod
    def _create_ollama_embeddings(config: Dict[str, Any]) -> Embeddings:
        """Create Ollama embeddings instance."""
        model = config.get('model', os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text'))
        base_url = config.get('base_url', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
        
        return OllamaEmbeddings(
            model=model,
            base_url=base_url
        )
    
    @staticmethod
    def _create_openrouter_embeddings(config: Dict[str, Any]) -> Embeddings:
        """Create OpenRouter embeddings instance (uses OpenAI-compatible API)."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError("langchain-openai is required for OpenRouter embeddings. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        
        # Ensure model is a string - handle cases where it might be an object or None
        model_raw = config.get('model')
        logger.debug(f"OpenRouter embeddings model_raw: {model_raw} (type: {type(model_raw).__name__})")
        
        if model_raw is None:
            model = 'openai/text-embedding-3-small'
        elif isinstance(model_raw, dict):
            # If model is an object, try to extract the id, name, or model field
            model = (model_raw.get('id') or 
                    model_raw.get('name') or 
                    model_raw.get('model') or 
                    'openai/text-embedding-3-small')
            # Ensure we got a string value, not another object
            if isinstance(model, dict):
                # If still a dict, try to extract from it recursively
                model = model.get('id') or model.get('name') or str(model)
            model = str(model) if model else 'openai/text-embedding-3-small'
        elif isinstance(model_raw, str):
            # If it's already a string, use it directly
            model = model_raw
        else:
            # For any other type, convert to string
            model = str(model_raw)
        
        # Final validation - ensure model is a non-empty string
        if not model or not isinstance(model, str) or model.strip() == '':
            logger.warning(f"Invalid model value '{model}', using default")
            model = 'openai/text-embedding-3-small'
        
        # Final check - if model contains "[object Object]", it means something went wrong
        if "[object Object]" in str(model) or model == "[object Object]":
            logger.warning(f"Detected '[object Object]' in model value, using default")
            model = 'openai/text-embedding-3-small'
        
        # Ensure model is clean string (remove any whitespace)
        model = str(model).strip()
        
        # Log for debugging
        logger.debug(f"OpenRouter embeddings final model: {model} (type: {type(model).__name__})")
        
        base_url = config.get('base_url', 'https://openrouter.ai/api/v1')
        
        # Double-check before passing to OpenAIEmbeddings
        if not isinstance(model, str) or model == "":
            logger.error(f"Invalid model after processing: {model}, using default")
            model = 'openai/text-embedding-3-small'
        
        # Final sanity check - log what we're about to send
        logger.info(f"Creating OpenAIEmbeddings with model='{model}' (type: {type(model).__name__}), base_url='{base_url}'")
        
        # One final check - if model is still "[object Object]", force default
        if model == "[object Object]" or (isinstance(model, str) and "[object Object]" in model):
            logger.error(f"CRITICAL: Model is still '[object Object]' at OpenAIEmbeddings creation, forcing default")
            model = 'openai/text-embedding-3-small'
        
        # Ensure model is definitely a string and not any other type
        # This is a last-ditch effort to prevent any object from being passed
        if not isinstance(model, str):
            logger.error(f"CRITICAL: Model is not a string at final check: {type(model).__name__}, value: {model}")
            model = 'openai/text-embedding-3-small'
        
        # Create a fresh string copy to ensure no object references
        model_str = str(model)
        if model_str == "[object Object]":
            logger.error(f"CRITICAL: String conversion resulted in '[object Object]', using default")
            model_str = 'openai/text-embedding-3-small'
        
        logger.info(f"Final model string: '{model_str}' (length: {len(model_str)})")
        
        return OpenAIEmbeddings(
            model=model_str,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
    
    @staticmethod
    def _create_openai_embeddings(config: Dict[str, Any]) -> Embeddings:
        """Create OpenAI embeddings instance."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError("langchain-openai is required for OpenAI embeddings. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        model = config.get('model', 'text-embedding-3-small')
        
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key
        )
    
    @staticmethod
    def _create_azure_openai_embeddings(config: Dict[str, Any]) -> Embeddings:
        """Create Azure OpenAI embeddings instance."""
        try:
            from langchain_openai import AzureOpenAIEmbeddings
        except ImportError:
            raise ImportError("langchain-openai is required for Azure OpenAI embeddings. Install it with: pip install langchain-openai")
        
        api_key = config.get('api_key') or os.getenv('AZURE_OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Azure OpenAI API key is required")
        
        azure_endpoint = config.get('azure_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT')
        if not azure_endpoint:
            raise ValueError("Azure OpenAI endpoint is required")
        
        deployment_name = config.get('deployment_name') or config.get('model')
        if not deployment_name:
            raise ValueError("Azure OpenAI deployment name is required")
        
        api_version = config.get('api_version', '2024-02-15-preview')
        
        return AzureOpenAIEmbeddings(
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_name,
            api_key=api_key,
            api_version=api_version
        )
    
    @staticmethod
    def _create_google_embeddings(config: Dict[str, Any]) -> Embeddings:
        """Create Google embeddings instance."""
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ImportError("langchain-google-genai is required for Google embeddings. Install it with: pip install langchain-google-genai")
        
        api_key = config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key is required")
        
        model = config.get('model', 'models/embedding-001')
        
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key
        )

