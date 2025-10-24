"""
OLLama integration service for local LLM embeddings and response generation.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = "C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct"
EMBEDDING_DIM = 384


class OllamaService:
    """Service for interacting with local OLLama model for embeddings and responses."""

    def __init__(self, model_path: Optional[str] = None, embedding_dim: int = EMBEDDING_DIM):
        """
        Initialize OLLama service.
        
        Args:
            model_path: Path to OLLama model directory
            embedding_dim: Dimension of embedding vectors (default 384)
        """
        self.model_path = Path(model_path or os.getenv("OLLAMA_MODEL_PATH", DEFAULT_MODEL_PATH))
        self.embedding_dim = embedding_dim
        self.model_loaded = False
        self.embed_model = None  # base model for embeddings
        self.gen_model = None    # causal LM for generation
        self.tokenizer = None
        self.device = "cpu"
        
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the OLLama model and tokenizer."""
        try:
            # Avoid importing torchvision (not needed for text models) to sidestep NumPy ABI issues
            os.environ.setdefault("TRANSFORMERS_NO_TORCHVISION", "1")
            # Also avoid TensorFlow import path in transformers when not used
            os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
            # Check if model path exists
            if not self.model_path.exists():
                logger.warning(
                    f"OLLama model path does not exist: {self.model_path}. "
                    "Service will operate in fallback mode."
                )
                self.model_loaded = False
                return

            # Try to import transformers
            try:
                from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer
            except ImportError:
                logger.warning(
                    "transformers library not available. "
                    "Install with: pip install transformers torch"
                )
                self.model_loaded = False
                return

            logger.info(f"Loading OLLama model from {self.model_path}")
            
            # Load tokenizer and models
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))

            # Ensure a pad token exists for padding operations (common for decoder-only LLMs)
            added_pad_token = False
            if self.tokenizer.pad_token is None:
                # Prefer EOS token as pad if available; otherwise add a new [PAD]
                if getattr(self.tokenizer, "eos_token", None):
                    self.tokenizer.pad_token = self.tokenizer.eos_token  # type: ignore[attr-defined]
                else:
                    self.tokenizer.add_special_tokens({"pad_token": "[PAD]"})
                    added_pad_token = True

            # Base model for hidden states/embeddings
            self.embed_model = AutoModel.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )

            # Causal LM for text generation (may be the same underlying architecture)
            try:
                self.gen_model = AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    trust_remote_code=True
                )
            except Exception as gen_exc:
                # If a generation head is not available, keep generation disabled
                logger.warning(f"Causal LM head unavailable for generation: {gen_exc}")
                self.gen_model = None

            # If we added a new special token (e.g. PAD), resize embeddings to match tokenizer vocab
            if added_pad_token:
                try:
                    if self.embed_model is not None and hasattr(self.embed_model, "resize_token_embeddings"):
                        self.embed_model.resize_token_embeddings(len(self.tokenizer))
                    if self.gen_model is not None and hasattr(self.gen_model, "resize_token_embeddings"):
                        self.gen_model.resize_token_embeddings(len(self.tokenizer))
                except Exception as resize_exc:
                    logger.warning(f"Failed to resize token embeddings after adding PAD: {resize_exc}")
            
            # Move to CPU (or GPU if available)
            try:
                import torch  # noqa: F401
                self.device = "cpu"  # Force CPU usage per deployment preference
                if self.embed_model is not None:
                    self.embed_model = self.embed_model.to(self.device)
                if self.gen_model is not None:
                    self.gen_model = self.gen_model.to(self.device)
                logger.info(f"Model(s) loaded successfully on {self.device}")
            except ImportError:
                logger.info("Model(s) loaded successfully (torch not available for device management)")
            
            self.model_loaded = True
            
        except Exception as exc:
            logger.error(f"Failed to initialize OLLama model: {exc}", exc_info=True)
            self.model_loaded = False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding, or None if generation fails
        """
        if not text or not text.strip():
            return self._zero_vector()

        if not self.model_loaded or self.embed_model is None:
            logger.warning("Model not loaded, returning zero vector")
            return self._zero_vector()

        try:
            import torch
            
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to same device as model
            device = next(self.embed_model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.embed_model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
            # Convert to list and ensure correct dimension
            embedding_vector = embeddings[0].cpu().tolist()
            
            # Adjust dimension if needed
            embedding_vector = self._adjust_dimension(embedding_vector)
            
            return embedding_vector
            
        except Exception as exc:
            logger.error(f"Error generating embedding: {exc}", exc_info=True)
            return self._zero_vector()

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        if not self.model_loaded or self.embed_model is None:
            logger.warning("Model not loaded, returning zero vectors")
            return [self._zero_vector() for _ in texts]

        try:
            import torch
            
            # Tokenize all inputs
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to same device as model
            device = next(self.embed_model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.embed_model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
            # Convert to list
            embedding_vectors = embeddings.cpu().tolist()
            
            # Adjust dimensions
            embedding_vectors = [
                self._adjust_dimension(vec) for vec in embedding_vectors
            ]
            
            return embedding_vectors
            
        except Exception as exc:
            logger.error(f"Error in batch embedding: {exc}", exc_info=True)
            return [self._zero_vector() for _ in texts]

    def generate_response(self, query: str, context: str) -> str:
        """
        Generate a contextual response using the OLLama model.
        
        Args:
            query: User's question or query
            context: Relevant context to inform the response
            
        Returns:
            Generated response text
        """
        if not self.model_loaded or self.gen_model is None:
            return (
                "I'm unable to generate a response right now as the AI model is not available. "
                "Please check the model configuration."
            )

        try:
            # Build prompt
            prompt = self._build_prompt(query, context)
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            )
            
            # Move to device
            device = next(self.gen_model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate response
            import torch
            with torch.no_grad():
                outputs = self.gen_model.generate(
                    **inputs,
                    max_new_tokens=400,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id or getattr(self.tokenizer, "eos_token_id", None)
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract response (remove prompt)
            if len(response) > len(prompt):
                response = response[len(prompt):].strip()
            
            return response if response else "I couldn't generate a meaningful response."
            
        except Exception as exc:
            logger.error(f"Error generating response: {exc}", exc_info=True)
            return (
                "I encountered an error while generating a response. "
                "Please try again or check the system logs."
            )

    def _build_prompt(self, query: str, context: str) -> str:
        """Build a structured prompt for the model."""
        return f"""Context information:
{context}

User question: {query}

Based on the context above, provide a helpful and accurate response:"""

    def _adjust_dimension(self, vector: List[float]) -> List[float]:
        """
        Adjust vector dimension to match target embedding dimension.
        
        Args:
            vector: Input vector
            
        Returns:
            Vector adjusted to target dimension
        """
        current_dim = len(vector)
        
        if current_dim == self.embedding_dim:
            return vector
        
        if current_dim < self.embedding_dim:
            # Pad with zeros
            return vector + [0.0] * (self.embedding_dim - current_dim)
        
        # Truncate to target dimension
        return vector[:self.embedding_dim]

    def _zero_vector(self) -> List[float]:
        """Return a zero vector of the target dimension."""
        return [0.0] * self.embedding_dim

    def is_available(self) -> bool:
        """Check if the OLLama service is available and ready."""
        return self.model_loaded

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_path": str(self.model_path),
            "embedding_dim": self.embedding_dim,
            "model_loaded": self.model_loaded,
            "model_exists": self.model_path.exists(),
        }

    def compare_embeddings(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compare two embeddings using cosine similarity.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
            1.0 = identical, 0.0 = orthogonal, values > 0.95 indicate very similar content
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        if len(embedding1) != len(embedding2):
            logger.warning(
                f"Embedding dimension mismatch: {len(embedding1)} vs {len(embedding2)}"
            )
            return 0.0
        
        try:
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1, dtype=float)
            vec2 = np.array(embedding2, dtype=float)
            
            # Calculate cosine similarity
            # cos(θ) = (A · B) / (||A|| × ||B||)
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Avoid division by zero
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Clamp to [0, 1] range (should already be, but just in case of numerical errors)
            similarity = max(0.0, min(1.0, float(similarity)))
            
            return similarity
            
        except Exception as exc:
            logger.error(f"Error comparing embeddings: {exc}", exc_info=True)
            return 0.0


