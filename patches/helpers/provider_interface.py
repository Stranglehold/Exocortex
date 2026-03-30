"""
provider_interface.py: Unified interface for LLM providers
Implements Provider Abstraction Pattern (Phase 3) based on Helios provider architecture
Supports Claude, OpenAI, and local models through single interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Iterator
from dataclasses import dataclass
import json

@dataclass
class ProviderConfig:
    """Configuration for a provider instance"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "default"
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 16384
    additional_kwargs: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_kwargs is None:
            self.additional_kwargs = {}

@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # "user", "assistant", "system"
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

@dataclass
class ChatResponse:
    """Represents a response from the provider"""
    content: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    model: str
    finish_reason: Optional[str] = None

class Provider(ABC):
    """Abstract base class for all LLM providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send chat messages and get response"""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream chat response token by token"""
        pass

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass

    def name(self) -> str:
        """Return provider name"""
        return self.__class__.__name__

class ClaudeProvider(Provider):
    """Anthropic Claude provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Default Claude settings
        if not config.model:
            self.config.model = "claude-3-5-sonnet-latest"

    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send request to Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                if msg.role == "system":
                    continue  # Handle system separately
                anthropic_messages.append(msg.to_dict())

            system_prompt = next((m.content for m in messages if m.role == "system"), "")

            response = client.messages.create(
                model=self.config.model,
                messages=anthropic_messages,
                system=system_prompt if system_prompt else None,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            return ChatResponse(
                content=response.content[0].text,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                model=self.config.model,
                finish_reason=response.stop_reason
            )
        except ImportError:
            raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")

    def chat_stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream response from Claude"""
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

            anthropic_messages = [m.to_dict() for m in messages if m.role != "system"]
            system_prompt = next((m.content for m in messages if m.role == "system"), "")

            with client.messages.stream(
                model=self.config.model,
                messages=anthropic_messages,
                system=system_prompt if system_prompt else None,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ) as stream:
                for chunk in stream:
                    if hasattr(chunk, "delta") and chunk.delta and hasattr(chunk.delta, "text"):
                        yield chunk.delta.text
        except ImportError:
            raise RuntimeError("anthropic package not installed")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Claude doesn't support embeddings directly - use alternative"""
        raise NotImplementedError("Claude does not support embeddings. Use OpenAI or local provider.")

class OpenAIProvider(Provider):
    """OpenAI provider implementation (also works with compatible APIs)"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.model:
            self.config.model = "gpt-4o-mini"

    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send request to OpenAI API"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

            response = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **self.config.additional_kwargs
            )

            return ChatResponse(
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )
        except ImportError:
            raise RuntimeError("openai package not installed. Install with: pip install openai")

    def chat_stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream response from OpenAI"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

            response = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True,
                **self.config.additional_kwargs
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except ImportError:
            raise RuntimeError("openai package not installed")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )

            return [item.embedding for item in response.data]
        except ImportError:
            raise RuntimeError("openai package not installed")

class LocalProvider(Provider):
    """Local model provider via LM Studio or similar"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            self.config.base_url = "http://host.docker.internal:1234/v1"
        if not config.model:
            self.config.model = "default"

    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send request to local model"""
        return OpenAIProvider(self.config).chat(messages)

    def chat_stream(self, messages: List[ChatMessage]) -> Iterator[str]:
        """Stream from local model"""
        return OpenAIProvider(self.config).chat_stream(messages)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings via local model"""
        return OpenAIProvider(self.config).embed(texts)

class ProviderFactory:
    """Factory for creating provider instances"""

    PROVIDERS = {
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,
        "openai": OpenAIProvider,
        "local": LocalProvider,
    }

    @classmethod
    def create(cls, provider_type: str, config: ProviderConfig) -> Provider:
        """Create a provider instance"""
        provider_class = cls.PROVIDERS.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(cls.PROVIDERS.keys())}")
        return provider_class(config)

    @classmethod
    def list_available(cls) -> List[str]:
        """List available provider types"""
        return list(cls.PROVIDERS.keys())
