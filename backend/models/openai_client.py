"""
OpenAI API client wrapper with retry logic, cost tracking, and error handling.

This module provides a robust interface to OpenAI's API with exponential
backoff, fallback strategies, and comprehensive error handling.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, AuthenticationError
from loguru import logger


# Initialize OpenAI client
_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """
    Get or create the global OpenAI client instance.

    Returns:
        Configured AsyncOpenAI client

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    global _openai_client

    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )

        _openai_client = AsyncOpenAI(api_key=api_key)
        logger.info("[OpenAI] Client initialized")

    return _openai_client


async def get_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o",
    temperature: float = 0.2,
    max_tokens: int = 2000,
    max_retries: int = 3
) -> str:
    """
    Get a completion from OpenAI with retry logic and error handling.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: OpenAI model name (default: gpt-4o)
        temperature: Sampling temperature (0.0 - 2.0)
        max_tokens: Maximum tokens in response
        max_retries: Maximum number of retry attempts for rate limits

    Returns:
        Text content of the completion

    Raises:
        Exception: If all retries fail or non-retryable error occurs
    """
    client = get_openai_client()

    for attempt in range(max_retries):
        try:
            logger.debug(
                f"[OpenAI] Requesting completion (model={model}, "
                f"temp={temperature}, max_tokens={max_tokens}, attempt={attempt + 1})"
            )

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content
            content = response.choices[0].message.content

            # Log usage stats
            usage = response.usage
            if usage:
                logger.info(
                    f"[OpenAI] Completion successful - "
                    f"prompt_tokens={usage.prompt_tokens}, "
                    f"completion_tokens={usage.completion_tokens}, "
                    f"total_tokens={usage.total_tokens}"
                )

            return content

        except RateLimitError as e:
            # Exponential backoff for rate limits
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s, 8s...
                logger.warning(
                    f"[OpenAI] Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[OpenAI] Rate limit exceeded after {max_retries} attempts")
                raise Exception(
                    "OpenAI rate limit exceeded. Please try again later or "
                    "consider upgrading your API plan."
                ) from e

        except APIConnectionError as e:
            # Network/connection errors
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1
                logger.warning(
                    f"[OpenAI] Connection error (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[OpenAI] Connection failed after {max_retries} attempts")
                raise Exception(
                    "Failed to connect to OpenAI API. Please check your internet "
                    "connection and try again."
                ) from e

        except AuthenticationError as e:
            # API key issues - don't retry
            logger.error(f"[OpenAI] Authentication failed: {e}")
            raise Exception(
                "OpenAI API authentication failed. Please check your OPENAI_API_KEY "
                "in the .env file."
            ) from e

        except Exception as e:
            # Other errors
            logger.error(f"[OpenAI] Unexpected error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}") from e

    # Should never reach here, but just in case
    raise Exception("OpenAI request failed after all retries")


async def get_completion_with_fallback(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o",
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> tuple[str, str]:
    """
    Get a completion with automatic fallback to HuggingFace if OpenAI fails.

    Args:
        messages: List of message dicts
        model: OpenAI model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        Tuple of (content, source) where source is "openai" or "huggingface"
    """
    try:
        content = await get_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return content, "openai"

    except Exception as e:
        logger.warning(f"[OpenAI] Failed, attempting HuggingFace fallback: {e}")

        try:
            from .hf_client import hf_fallback_completion

            # Convert messages to single prompt for HF
            prompt = _messages_to_prompt(messages)

            content = await hf_fallback_completion(prompt, max_tokens=max_tokens)
            return content, "huggingface"

        except Exception as hf_error:
            logger.error(f"[HuggingFace] Fallback also failed: {hf_error}")
            raise Exception(
                "Both OpenAI and HuggingFace completions failed. "
                "Please check your API keys and try again."
            ) from e


def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    """
    Convert OpenAI message format to a single prompt string.

    Args:
        messages: List of message dicts with role and content

    Returns:
        Formatted prompt string
    """
    prompt_parts = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")

    return "\n\n".join(prompt_parts)


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str = "gpt-4o") -> float:
    """
    Estimate the cost of an API call in USD.

    Prices as of January 2025 (these should be updated periodically):
    - GPT-4o: $2.50 / 1M input tokens, $10.00 / 1M output tokens
    - GPT-4o-mini: $0.15 / 1M input tokens, $0.60 / 1M output tokens

    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        model: Model name

    Returns:
        Estimated cost in USD
    """
    # Pricing per 1M tokens
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    model_pricing = pricing.get(model, pricing["gpt-4o"])

    input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost
