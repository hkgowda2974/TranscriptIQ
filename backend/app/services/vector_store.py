import math
import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from backend.app.schemas import TranscriptChunk
from backend.app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Vector Store & Retrieval Service for expert transcript dialogue chunks.
    Supports dense embeddings via Google Gemini (`text-embedding-004`) with an in-memory
    vector index and metadata filtering (`expert_id`, `market`, `source_file`).
    """

    def __init__(self):
        self.chunks: List[TranscriptChunk] = []
        self.vectors: List[List[float]] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _generate_fallback_embedding(self, text: str, dimensions: int = 128) -> List[float]:
        """
        Generates a deterministic term-frequency vector normalized to L2 norm
        when external API key is unconfigured.
        """
        tokens = self._tokenize(text)
        freq: Dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1

        vec = [0.0] * dimensions
        for word, count in freq.items():
            # Hash trick to map vocabulary terms to fixed dimensions
            h = abs(hash(word)) % dimensions
            vec[h] += float(count)

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generates dense vector embeddings using Google Gemini API (`text-embedding-004`)
        or fallback term-frequency embedding.
        """
        if GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                    return list(response.embedding.values)
                elif isinstance(response, dict) and "embedding" in response:
                    return list(response["embedding"]["values"])
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Falling back to local vectorizer.")

        return self._generate_fallback_embedding(text)

    def add_chunks(self, chunks: List[TranscriptChunk]) -> None:
        """
        Embeds and indexes a list of TranscriptChunks into vector memory.
        """
        for chunk in chunks:
            text_to_embed = f"{chunk.question_context}\n{chunk.verbatim_text}"
            vec = self._generate_embedding(text_to_embed)
            self.chunks.append(chunk)
            self.vectors.append(vec)
        logger.info(f"Indexed {len(chunks)} chunks into vector store. Total chunks: {len(self.chunks)}.")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Computes dot product cosine similarity between two normalized vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        return sum(a * b for a, b in zip(vec1, vec2))

    def search(
        self,
        query: str,
        top_k: int = 5,
        expert_id: Optional[str] = None,
        market: Optional[str] = None
    ) -> List[TranscriptChunk]:
        """
        Retrieves top-K most semantically and lexically relevant TranscriptChunks for a query.
        Applies hybrid scoring (vector cosine similarity + term overlap boost + query-intent concept match).
        """
        if not self.chunks:
            logger.warning("Vector store search called on empty index.")
            return []

        from backend.app.services.intent_detector import detect_query_intent
        intent = detect_query_intent(query)

        query_lower = query.lower()
        query_words = set(self._tokenize(query)) - {
            "what", "is", "are", "the", "in", "how", "does", "do", "to", "for", "a", "of",
            "and", "or", "on", "with", "about", "across", "hospitals", "tell", "me", "which"
        }

        # Auto-detect target markets from query if market parameter is not explicitly passed
        detected_markets = intent.markets
        if not market and len(detected_markets) == 1:
            market = detected_markets[0]

        query_vec = self._generate_embedding(query)
        scored_results: List[Tuple[float, TranscriptChunk]] = []

        for i, chunk in enumerate(self.chunks):
            # Apply explicit metadata filtering
            if expert_id and chunk.expert_id.lower() != expert_id.lower():
                continue
            if market and chunk.market.lower() != market.lower():
                continue

            vector_sim = self._cosine_similarity(query_vec, self.vectors[i])

            # Compute lexical keyword match score
            chunk_text_lower = f"{chunk.expert_name} {chunk.market} {chunk.question_context} {chunk.verbatim_text}".lower()
            chunk_words = set(self._tokenize(chunk_text_lower))
            overlap_count = len(query_words.intersection(chunk_words))
            lexical_score = min(1.0, overlap_count / max(1, len(query_words))) if query_words else 0.0

            # Compute query-intent concept alignment score
            concept_score = 0.0
            if intent.target_concepts:
                matching_concepts = [c for c in intent.target_concepts if c in chunk_text_lower]
                concept_score = min(1.0, len(matching_concepts) / max(1, min(3, len(intent.target_concepts))))

            # Negative concept penalty (e.g., procurement timelines appearing in training queries)
            penalty = 0.0
            if intent.negative_concepts:
                if any(nc in chunk_text_lower for nc in intent.negative_concepts):
                    penalty = 0.20

            # Market boost if query explicitly asks about specific market(s)
            market_boost = 0.0
            if detected_markets:
                if chunk.market.lower() in detected_markets:
                    market_boost = 0.35
                else:
                    market_boost = -0.25

            final_score = (0.35 * vector_sim) + (0.30 * lexical_score) + (0.35 * concept_score) - penalty + market_boost
            scored_results.append((final_score, chunk))

        # Sort descending by final hybrid score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        retrieved = [chunk for score, chunk in scored_results[:top_k]]
        logger.info(f"Query '{query[:30]}...' retrieved {len(retrieved)} chunks (Filters: expert_id={expert_id}, market={market}, intent={intent.primary_intent}).")
        return retrieved

    def clear(self) -> None:
        """Clears indexed chunks and vectors."""
        self.chunks.clear()
        self.vectors.clear()
        logger.info("Cleared vector store index.")


# Singleton service instance
vector_store = VectorStoreService()
