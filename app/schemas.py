"""
Pydantic schemas for API request/response validation.

This module defines the data transfer objects (DTOs) used for API
serialization and validation using Pydantic models.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, validator


class SearchResult(BaseModel):
    """
    Schema for semantic search results.
    
    Represents a single search result containing a relevant text chunk
    from a paper along with its metadata.
    
    Attributes:
        paper_title: The title of the source paper
        chunk_text: The relevant text chunk that matches the search query
        page_number: Page number where the chunk is located (optional)
        pdf_path: File path to the source PDF document (optional)
    """

    paper_title: str = Field(
        description="원본 논문 제목",
        min_length=1,
        max_length=500,
        example="Deep Learning for Natural Language Processing"
    )
    chunk_text: str = Field(
        description="검색된 관련 텍스트 조각",
        min_length=1,
        max_length=5000,
        example="이 연구에서는 자연어 처리를 위한 딥러닝 기법을 제시합니다..."
    )
    page_number: int | None = Field(
        default=None,
        description="텍스트 조각이 위치한 페이지 번호",
        ge=1,
        example=15
    )
    pdf_path: str | None = Field(
        default=None,
        description="원본 PDF 파일 경로",
        example="data/pdfs/deep_learning_nlp.pdf"
    )

    model_config = ConfigDict(from_attributes=True)

    @validator('chunk_text')
    def validate_chunk_text(cls, v: str) -> str:
        """Validate chunk text is not empty or whitespace only."""
        if not v.strip():
            raise ValueError('Chunk text cannot be empty')
        return v.strip()


class PaperResponse(BaseModel):
    """
    Schema for paper metadata response.
    
    Represents a paper entity with its core metadata for API responses.
    
    Attributes:
        id: Unique identifier for the paper
        title: Paper title
        author: Primary author name (optional)
        publisher: Publisher/journal name (optional)
        publication_date: Publication date (optional)
        url: Original source URL (optional)
        pdf_path: Local PDF file path (optional)
        abstract: Paper abstract/summary (optional)
    """

    id: int = Field(
        description="논문 고유 식별자",
        example=12345
    )
    title: str = Field(
        description="논문 제목",
        min_length=1,
        max_length=500,
        example="머신러닝을 활용한 자연어 처리 기법 연구"
    )
    author: str | None = Field(
        default=None,
        description="주저자명",
        max_length=200,
        example="김철수"
    )
    publisher: str | None = Field(
        default=None,
        description="출판사/학회명",
        max_length=200,
        example="한국정보과학회"
    )
    publication_date: str | None = Field(
        default=None,
        description="출판일",
        example="2024-01-15"
    )
    url: str | None = Field(
        default=None,
        description="원본 논문 URL",
        example="https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE12345"
    )
    pdf_path: str | None = Field(
        default=None,
        description="PDF 파일 경로",
        example="data/pdfs/paper_12345.pdf"
    )
    abstract: str | None = Field(
        default=None,
        description="논문 초록",
        max_length=2000,
        example="본 연구는 자연어 처리 분야에서..."
    )

    model_config = ConfigDict(from_attributes=True)

    @validator('title')
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty or whitespace only."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class PaperCreateRequest(BaseModel):
    """
    Schema for creating new papers.
    
    Request schema for adding new papers to the database.
    """

    title: str = Field(
        description="논문 제목",
        min_length=1,
        max_length=500
    )
    author: str | None = Field(
        default=None,
        description="저자명",
        max_length=200
    )
    publisher: str | None = Field(
        default=None,
        description="출판사",
        max_length=200
    )
    publication_date: str | None = Field(
        default=None,
        description="출판일 (YYYY-MM-DD 형식)"
    )
    url: str | None = Field(
        default=None,
        description="원본 URL"
    )
    abstract: str | None = Field(
        default=None,
        description="논문 초록",
        max_length=2000
    )


class SearchStatsResponse(BaseModel):
    """
    Schema for search statistics response.
    
    Contains metrics about search performance and results.
    """

    total_results: int = Field(
        description="전체 검색 결과 수",
        ge=0,
        example=42
    )
    search_time_ms: float = Field(
        description="검색 소요 시간 (밀리초)",
        ge=0,
        example=156.7
    )
    query: str = Field(
        description="검색 쿼리",
        example="딥러닝"
    )


class PaperStatsResponse(BaseModel):
    """
    Schema for paper database statistics.
    
    Provides overview statistics about the paper collection.
    """

    total_papers: int = Field(
        description="전체 논문 수",
        ge=0,
        example=15432
    )
    papers_with_pdf: int = Field(
        description="PDF가 있는 논문 수",
        ge=0,
        example=12890
    )
    papers_without_pdf: int = Field(
        description="PDF가 없는 논문 수",
        ge=0,
        example=2542
    )
    pdf_coverage_percentage: float = Field(
        description="PDF 커버리지 비율 (%)",
        ge=0,
        le=100,
        example=83.5
    )


class HealthCheckResponse(BaseModel):
    """
    Schema for health check response.
    
    Indicates the current status of the application.
    """

    status: str = Field(
        description="서비스 상태",
        example="ok"
    )
    version: str | None = Field(
        default=None,
        description="API 버전",
        example="0.4.0"
    )
    timestamp: str | None = Field(
        default=None,
        description="응답 시간",
        example="2024-01-15T10:30:00Z"
    )
