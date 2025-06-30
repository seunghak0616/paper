"""
Search service for semantic paper search.
"""


import openai
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import EmbeddingError, SearchError, validate_search_query
from app.repositories import ChunkRepository, PaperRepository
from app.schemas import SearchResult


class SearchService:
    """Service for semantic search operations."""

    def __init__(self, db: Session):
        self.db = db
        self.chunk_repo = ChunkRepository(db)
        self.paper_repo = PaperRepository(db)
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float | None = None
    ) -> list[SearchResult]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            similarity_threshold: Optional minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        try:
            # Validate query
            query = validate_search_query(query)

            # Generate embedding
            query_embedding = self._generate_embedding(query)

            # Search similar chunks
            similar_chunks = self.chunk_repo.search_similar_by_embedding(
                query_embedding=query_embedding,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            # Convert to SearchResult objects
            results = []
            for chunk in similar_chunks:
                if chunk.paper:  # Paper should be loaded via joinedload
                    results.append(SearchResult(
                        paper_title=chunk.paper.title,
                        chunk_text=chunk.chunk_text,
                        page_number=chunk.page_number,
                        pdf_path=chunk.paper.pdf_path
                    ))

            return results

        except Exception as e:
            if isinstance(e, (SearchError, EmbeddingError)):
                raise
            raise SearchError(detail=str(e))

    def text_search(
        self,
        query: str,
        limit: int = 10
    ) -> list[SearchResult]:
        """
        Perform text-based search (full-text search).
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        try:
            # Validate query
            query = validate_search_query(query)

            # Search chunks by text
            matching_chunks = self.chunk_repo.search_by_text(
                query=query,
                limit=limit
            )

            # Convert to SearchResult objects
            results = []
            for chunk in matching_chunks:
                if chunk.paper:  # Paper should be loaded via joinedload
                    results.append(SearchResult(
                        paper_title=chunk.paper.title,
                        chunk_text=chunk.chunk_text,
                        page_number=chunk.page_number,
                        pdf_path=chunk.paper.pdf_path
                    ))

            return results

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(detail=str(e))

    def hybrid_search(
        self,
        query: str,
        semantic_weight: float = 0.7,
        text_weight: float = 0.3,
        limit: int = 10
    ) -> list[SearchResult]:
        """
        Perform hybrid search combining semantic and text search.
        
        Args:
            query: Search query text
            semantic_weight: Weight for semantic search results
            text_weight: Weight for text search results
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        try:
            # Get semantic search results
            semantic_results = self.semantic_search(query, limit=limit * 2)

            # Get text search results
            text_results = self.text_search(query, limit=limit * 2)

            # Combine and deduplicate results
            # This is a simple implementation - could be enhanced with
            # proper ranking algorithms
            seen_chunks = set()
            combined_results = []

            # Add semantic results first (higher weight)
            for result in semantic_results:
                chunk_key = (result.paper_title, result.chunk_text)
                if chunk_key not in seen_chunks:
                    seen_chunks.add(chunk_key)
                    combined_results.append(result)

            # Add text results that weren't already included
            for result in text_results:
                chunk_key = (result.paper_title, result.chunk_text)
                if chunk_key not in seen_chunks:
                    seen_chunks.add(chunk_key)
                    combined_results.append(result)

            return combined_results[:limit]

        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(detail=str(e))

    def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=settings.embedding_model
            )
            return response.data[0].embedding

        except Exception as e:
            raise EmbeddingError(detail=f"Failed to generate embedding: {str(e)}")

    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> list[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        try:
            if len(partial_query.strip()) < 2:
                return []

            # Simple implementation: search paper titles and return unique terms
            papers = self.paper_repo.search_by_text(partial_query, limit=limit * 2)

            suggestions = []
            seen_terms = set()

            for paper in papers:
                # Extract meaningful terms from title
                words = paper.title.split()
                for word in words:
                    clean_word = word.strip('.,!?;:').lower()
                    if (len(clean_word) >= 3 and
                        clean_word not in seen_terms and
                        partial_query.lower() in clean_word):
                        seen_terms.add(clean_word)
                        suggestions.append(clean_word)

                        if len(suggestions) >= limit:
                            break

                if len(suggestions) >= limit:
                    break

            return suggestions

        except Exception:
            # Don't raise error for suggestions - just return empty list
            return []
