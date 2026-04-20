"""Moonshot AI (Kimi) client wrapper using OpenAI-compatible API.

Moonshot AI provides an OpenAI-compatible chat completions API. This module
wraps the OpenAI client with Moonshot's base URL and default model, enabling
Second Brain OS agents to use Kimi models as an alternative to Anthropic Claude.

Environment:
    MOONSHOT_API_KEY: Required. Your Moonshot AI API key.

Default model: moonshot-v1-128k (128k context window, good for long context)
"""

import os
from typing import Any, Dict, List, Optional


def get_moonshot_client() -> Any:
    """Get an OpenAI client configured for Moonshot AI.

    Returns:
        OpenAI client instance pointing to Moonshot's API

    Raises:
        ImportError: If openai package is not installed
        ValueError: If MOONSHOT_API_KEY is not set
    """
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError(
            "Moonshot AI support requires the 'openai' package. "
            "Install it with: pip install openai"
        ) from e

    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise ValueError(
            "MOONSHOT_API_KEY environment variable is required for Moonshot AI."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1",
    )


class MoonshotChatCompletion:
    """Wrapper for Moonshot chat completions with Anthropic-like interface."""

    DEFAULT_MODEL = "moonshot-v1-128k"

    def __init__(self, client: Any = None, model: str = DEFAULT_MODEL):
        """Initialize Moonshot chat completion wrapper.

        Args:
            client: OpenAI client (auto-created if None)
            model: Model name to use
        """
        self.client = client or get_moonshot_client()
        self.model = model

    def create(
        self,
        system: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Create a chat completion.

        Provides an interface similar to Anthropic's messages.create() for
easy drop-in replacement in agents.

        Args:
            system: System prompt text
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with 'content' (list of text blocks) and 'usage' info
        """
        if messages is None:
            messages = []

        # Moonshot uses OpenAI format: system message is first user message
        # or a separate system role message
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Normalize to Anthropic-like response shape
        return {
            "content": [{"type": "text", "text": response.choices[0].message.content}],
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        }


class MoonshotClient:
    """High-level Moonshot client mimicking Anthropic client interface."""

    def __init__(self, api_key: str = None, model: str = "moonshot-v1-128k"):
        """Initialize Moonshot client.

        Args:
            api_key: Moonshot API key (defaults to MOONSHOT_API_KEY env var)
            model: Model name
        """
        if api_key:
            os.environ.setdefault("MOONSHOT_API_KEY", api_key)

        self.client = get_moonshot_client()
        self.model = model
        self.messages = MoonshotChatCompletion(self.client, model)
