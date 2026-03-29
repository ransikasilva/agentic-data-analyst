"""
HuggingFace client for embeddings and fallback LLM completions.

This module provides:
1. Embeddings via sentence-transformers for semantic search
2. Fallback LLM completions via HuggingFace Inference API
"""

import os
from typing import List, Optional
from loguru import logger


# Global model instances (lazy loaded)
_embedding_model = None
_hf_inference_client = None


def get_embedding_model():
    """
    Get or create the sentence-transformers embedding model.

    Uses all-MiniLM-L6-v2: a lightweight, fast model for embeddings.

    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            logger.info(f"[HuggingFace] Loading embedding model: {model_name}")

            _embedding_model = SentenceTransformer(model_name)

            logger.info("[HuggingFace] Embedding model loaded successfully")

        except Exception as e:
            logger.error(f"[HuggingFace] Failed to load embedding model: {e}")
            raise Exception(
                "Failed to initialize sentence-transformers model. "
                "Ensure the library is installed: pip install sentence-transformers"
            ) from e

    return _embedding_model


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (each vector is a list of floats)

    Raises:
        Exception: If embedding generation fails
    """
    if not texts:
        return []

    try:
        model = get_embedding_model()
        embeddings = model.encode(texts, show_progress_bar=False)

        # Convert numpy arrays to lists
        embeddings_list = [emb.tolist() for emb in embeddings]

        logger.debug(f"[HuggingFace] Generated embeddings for {len(texts)} texts")

        return embeddings_list

    except Exception as e:
        logger.error(f"[HuggingFace] Embedding generation failed: {e}")
        raise Exception(f"Failed to generate embeddings: {str(e)}") from e


def get_hf_inference_client():
    """
    Get or create the HuggingFace Inference API client.

    Returns:
        InferenceClient instance

    Raises:
        ValueError: If HF_TOKEN is not set
    """
    global _hf_inference_client

    if _hf_inference_client is None:
        try:
            from huggingface_hub import InferenceClient

            hf_token = os.getenv("HF_TOKEN")

            if not hf_token:
                logger.warning(
                    "[HuggingFace] HF_TOKEN not set. Inference API calls will be limited. "
                    "Set HF_TOKEN in .env for better access."
                )
                # Can still work without token but with rate limits
                hf_token = None

            _hf_inference_client = InferenceClient(token=hf_token)

            logger.info("[HuggingFace] Inference client initialized")

        except Exception as e:
            logger.error(f"[HuggingFace] Failed to create inference client: {e}")
            raise Exception(
                "Failed to initialize HuggingFace InferenceClient. "
                "Ensure huggingface_hub is installed: pip install huggingface_hub"
            ) from e

    return _hf_inference_client


async def hf_fallback_completion(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.2
) -> str:
    """
    Get a text completion from HuggingFace Inference API as fallback.

    Uses Mistral-7B-Instruct by default (configurable via HF_FALLBACK_MODEL env var).

    Args:
        prompt: Text prompt to complete
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        Generated text completion

    Raises:
        Exception: If inference fails
    """
    try:
        client = get_hf_inference_client()
        model = os.getenv("HF_FALLBACK_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

        logger.info(
            f"[HuggingFace] Requesting fallback completion "
            f"(model={model}, max_tokens={max_tokens})"
        )

        # Note: The InferenceClient API might be async in newer versions
        # For now, wrapping synchronous call
        import asyncio

        response = await asyncio.to_thread(
            client.text_generation,
            prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
            return_full_text=False  # Only return generated text, not prompt
        )

        logger.info(
            f"[HuggingFace] Fallback completion successful ({len(response)} chars)"
        )

        return response

    except Exception as e:
        logger.error(f"[HuggingFace] Inference failed: {e}")
        raise Exception(f"HuggingFace inference error: {str(e)}") from e


def embed_dataset_columns(column_names: List[str], column_dtypes: dict) -> dict:
    """
    Create embeddings for dataset columns for semantic search.

    This can be used later for intelligent column selection based on
    natural language queries.

    Args:
        column_names: List of column names
        column_dtypes: Dict mapping column names to data types

    Returns:
        Dict mapping column names to embedding vectors
    """
    if not column_names:
        return {}

    try:
        # Create descriptive text for each column
        column_descriptions = [
            f"{name} (type: {column_dtypes.get(name, 'unknown')})"
            for name in column_names
        ]

        # Generate embeddings
        embeddings = get_embeddings(column_descriptions)

        # Create mapping
        column_embeddings = {
            name: emb
            for name, emb in zip(column_names, embeddings)
        }

        logger.debug(f"[HuggingFace] Embedded {len(column_names)} columns")

        return column_embeddings

    except Exception as e:
        logger.error(f"[HuggingFace] Column embedding failed: {e}")
        return {}
