"""
SQLAlchemy database models for the Papers API.

This module defines the database schema using SQLAlchemy ORM models
for storing academic papers and their associated text chunks with
vector embeddings for semantic search.
"""

from __future__ import annotations

import datetime
import os

from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import Mapped, declarative_base, relationship, sessionmaker

from app.config import settings

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variables
# Docker Compose uses 'db' host, local development uses 'localhost'
DATABASE_URL = os.getenv(
    "DATABASE_URL", settings.database_url
)

# Database engine and session configuration
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Paper(Base):
    """
    Model representing an academic paper.
    
    This model stores metadata about academic papers including bibliographic
    information, PDF file paths, and vector embeddings for semantic search.
    
    Attributes:
        id: Primary key identifier
        title: Paper title (required, indexed)
        author: Primary author name
        publisher: Publisher or journal name
        publication_date: Publication date
        url: Original source URL
        pdf_path: Local path to downloaded PDF file
        abstract: Paper abstract or summary
        created_at: Record creation timestamp
        chunks: Related text chunks for this paper
    """

    __tablename__ = "papers"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String, nullable=False, index=True)
    author: Mapped[str | None] = Column(String)
    publisher: Mapped[str | None] = Column(String)
    publication_date: Mapped[str | None] = Column(String)  # Store as string for flexibility
    url: Mapped[str | None] = Column(String, unique=True)  # Unique constraint for source URLs
    pdf_path: Mapped[str | None] = Column(String)
    abstract: Mapped[str | None] = Column(Text)
    created_at: Mapped[datetime.datetime] = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    # Relationship to paper chunks
    chunks: Mapped[list[PaperChunk]] = relationship(
        "PaperChunk",
        back_populates="paper",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of the Paper model."""
        return f"<Paper(id={self.id}, title='{self.title[:50]}...')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.title


class PaperChunk(Base):
    """
    Model representing a text chunk from a paper.
    
    This model stores segmented text chunks from papers along with their
    vector embeddings for semantic search. Chunks are created by splitting
    long paper texts into smaller, more manageable pieces to improve
    retrieval accuracy in RAG (Retrieval-Augmented Generation) systems.
    
    Attributes:
        id: Primary key identifier
        paper_id: Foreign key reference to the parent paper
        chunk_text: The actual text content of this chunk
        page_number: Page number where this chunk originates
        embedding: Vector embedding for semantic search (1536 dimensions)
        paper: Relationship to the parent Paper model
    """

    __tablename__ = "paper_chunks"

    id: Mapped[int] = Column(Integer, primary_key=True)
    paper_id: Mapped[int] = Column(Integer, ForeignKey("papers.id"), nullable=False)
    chunk_text: Mapped[str] = Column(Text, nullable=False)
    page_number: Mapped[int | None] = Column(Integer)
    # Vector embedding for semantic search (OpenAI ada-002: 1536 dimensions)
    embedding: Mapped[list[float] | None] = Column(Vector(1536))

    # Relationship to parent paper
    paper: Mapped[Paper] = relationship("Paper", back_populates="chunks")

    # HNSW index for efficient vector similarity search
    __table_args__ = (
        Index(
            "ix_paper_chunks_embedding",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )

    def __repr__(self) -> str:
        """String representation of the PaperChunk model."""
        preview = self.chunk_text[:50] + "..." if len(self.chunk_text) > 50 else self.chunk_text
        return f"<PaperChunk(id={self.id}, paper_id={self.paper_id}, page={self.page_number}, text='{preview}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Chunk from {self.paper.title if self.paper else 'Unknown'} (page {self.page_number})"


def create_db_and_tables() -> None:
    """
    Create database tables and enable required extensions.
    
    This function:
    1. Enables the pgvector extension for vector operations
    2. Creates all tables defined in the SQLAlchemy models
    
    Note:
        This should be called once during application setup.
        The pgvector extension must be available in the PostgreSQL instance.
    
    Raises:
        SQLAlchemyError: If database connection or table creation fails
    """
    with engine.connect() as conn:
        # Enable pgvector extension for vector operations
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Create all tables defined in Base metadata
    Base.metadata.create_all(bind=engine)
