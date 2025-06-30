from __future__ import annotations

import os
import re
from pathlib import Path

import openai
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core import get_logger, log_security_event, setup_logging
from app.dependencies import get_paper_service, get_search_service
from app.exceptions import (
    FileNotFoundError,
)
from app.models import PaperChunk, SessionLocal
from app.schemas import PaperResponse, SearchResult
from app.services import PaperService, SearchService

# --- 초기 설정 ---
# 로깅 설정 적용
setup_logging()
app_logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / settings.data_dir
PDF_DIR = BASE_DIR / settings.pdf_dir
META_PATH = DATA_DIR / "metadata.json"

# Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
app = FastAPI(title="DBpia 논문 API", version="0.4.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add logging middleware
# app.add_middleware(LoggingMiddleware) # 표준 logging에서는 다르게 처리해야 할 수 있음

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="public"), name="static")

# OpenAI 클라이언트
client = openai.OpenAI(api_key=settings.openai_api_key)
EMBEDDING_MODEL = settings.embedding_model

app_logger.info("Application initialized. Version: 0.4.0")

# CORS 미들웨어 (보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경을 위해 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 의존성 ---
# Note: Moved to app.dependencies module


# --- API 엔드포인트 ---

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/")
async def read_root():
    """루트 경로 접속 시 index.html 반환"""
    return FileResponse('public/index.html')


@app.get("/health")
async def health_check():
    """서비스 상태 체크"""
    return {"status": "ok"}


@app.get("/papers", response_model=list[PaperResponse])
async def list_papers(
    q: str | None = Query(None, description="논문 제목, 저자, 발행기관으로 검색"),
    skip: int = Query(0, description="건너뛸 항목 수", ge=0),
    limit: int = Query(10, description="반환할 최대 항목 수", ge=1, le=100),
    paper_service: PaperService = Depends(get_paper_service),
):
    """
    수집된 논문 메타데이터 목록을 페이지네이션과 검색 기능과 함께 반환합니다.
    """
    return paper_service.get_papers(
        skip=skip,
        limit=limit,
        search_query=q
    )


@app.post("/search", response_model=list[SearchResult])
async def search_papers(
    query: str = Query(..., description="검색할 질문", min_length=2, max_length=100),
    limit: int = Query(5, description="반환할 최대 결과 수", ge=1, le=20),
    search_service: SearchService = Depends(get_search_service),
):
    """
    질문을 임베딩으로 변환하고, DB에서 유사도가 높은 논문 청크를 검색합니다.
    """
    return search_service.semantic_search(query=query, limit=limit)


def send_bytes_range_requests(
    request: Request, file_path: Path, media_type: str
) -> Response:
    """대용량 파일에 대한 Range Request를 처리하고 StreamingResponse를 반환합니다."""
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    headers = {
        "content-type": media_type,
        "accept-ranges": "bytes",
        "content-encoding": "identity",
        "content-length": str(file_size),
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, content-range, content-encoding"
        ),
    }

    if range_header is None:
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=file_path.name,
            headers=headers,
        )

    byte1, byte2 = 0, file_size - 1
    if range_header:
        match = re.search(r"(\d+)-(\d*)", range_header)
        if match:
            groups = match.groups()
            byte1 = int(groups[0])
            if groups[1]:
                byte2 = int(groups[1])

    req_length = byte2 - byte1 + 1
    headers["content-length"] = str(req_length)
    headers["content-range"] = f"bytes {byte1}-{byte2}/{file_size}"

    return StreamingResponse(
        file_iterator(file_path, byte1, req_length),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
        media_type=media_type,
    )


def file_iterator(file_path: Path, offset: int, chunk_size: int):
    """파일의 특정 부분만 읽어오는 제너레이터"""
    with open(file_path, "rb") as f:
        f.seek(offset)
        yield f.read(chunk_size)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket을 통해 실시간 RAG 챗봇을 제공합니다.
    """
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            query = await websocket.receive_text()

            # 1. 벡터 검색으로 관련성 높은 컨텍스트 찾기
            response = client.embeddings.create(input=[query], model=EMBEDDING_MODEL)
            query_embedding = response.data[0].embedding
            similar_chunks = (
                db.query(PaperChunk)
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(3)
                .all()
            )
            context = "\n\n".join(
                [f"문서: {chunk.paper.title} (p.{chunk.page_number})\n내용: {chunk.chunk_text}" for chunk in similar_chunks]
            )

            # 2. LLM에 스트리밍 요청
            if not similar_chunks:
                await websocket.send_text("관련 정보를 찾을 수 없습니다.")
                await websocket.send_text("[DONE]")
                continue

            system_prompt = (
                "당신은 논문 검색 어시스턴트입니다. "
                "주어진 컨텍스트 정보를 바탕으로 사용자의 질문에 답변하세요. "
                "답변은 반드시 한국어로 작성하고, 컨텍스트에 없는 내용은 언급하지 마세요."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"컨텍스트:\n{context}\n\n질문: {query}"},
            ]

            stream = client.chat.completions.create(
                model="gpt-4o", # 또는 gpt-3.5-turbo
                messages=messages,
                stream=True,
            )

            # 3. 답변 스트리밍
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    await websocket.send_text(content)

            # 스트리밍 종료 표시
            await websocket.send_text("[DONE]")

    except WebSocketDisconnect:
        print("WebSocket 연결이 종료되었습니다.")
    except Exception as e:
        print(f"WebSocket 오류 발생: {e}")
        await websocket.send_text(f"오류가 발생했습니다: {e}")
    finally:
        db.close()


@app.get("/papers/{title}/pdf")
@limiter.limit("20/minute")
async def get_pdf(
    request: Request,
    title: str,
    paper_service: PaperService = Depends(get_paper_service)
):
    """논문 제목으로 PDF 스트리밍 (Range Request 지원)"""
    try:
        file_path = paper_service.get_paper_pdf_path(title)
        return send_bytes_range_requests(
            request, file_path=file_path, media_type="application/pdf"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 새로운 API 엔드포인트 ---

@app.get("/papers/stats")
async def get_paper_statistics(
    paper_service: PaperService = Depends(get_paper_service)
):
    """논문 데이터베이스 통계 정보 반환"""
    return paper_service.get_paper_statistics()


@app.get("/papers/recent", response_model=list[PaperResponse])
async def get_recent_papers(
    limit: int = Query(10, description="반환할 최대 항목 수", ge=1, le=50),
    paper_service: PaperService = Depends(get_paper_service)
):
    """최근 추가된 논문 목록 반환"""
    return paper_service.get_recent_papers(limit=limit)


@app.get("/papers/author/{author}", response_model=list[PaperResponse])
async def get_papers_by_author(
    author: str,
    skip: int = Query(0, description="건너뛸 항목 수", ge=0),
    limit: int = Query(10, description="반환할 최대 항목 수", ge=1, le=100),
    paper_service: PaperService = Depends(get_paper_service)
):
    """특정 저자의 논문 목록 반환"""
    return paper_service.get_papers_by_author(
        author=author,
        skip=skip,
        limit=limit
    )


@app.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="부분 검색어", min_length=2),
    limit: int = Query(5, description="제안 수", ge=1, le=10),
    search_service: SearchService = Depends(get_search_service)
):
    """검색어 자동완성 제안"""
    return {
        "suggestions": search_service.get_search_suggestions(q, limit=limit)
    }


@app.post("/search/text", response_model=list[SearchResult])
async def text_search_papers(
    query: str = Query(..., description="검색할 텍스트", min_length=2, max_length=100),
    limit: int = Query(10, description="반환할 최대 결과 수", ge=1, le=50),
    search_service: SearchService = Depends(get_search_service),
):
    """텍스트 기반 논문 검색 (전문 검색)"""
    return search_service.text_search(query=query, limit=limit)


@app.post("/search/hybrid", response_model=list[SearchResult])
async def hybrid_search_papers(
    query: str = Query(..., description="검색할 질문", min_length=2, max_length=100),
    limit: int = Query(10, description="반환할 최대 결과 수", ge=1, le=50),
    semantic_weight: float = Query(0.7, description="의미 검색 가중치", ge=0.0, le=1.0),
    text_weight: float = Query(0.3, description="텍스트 검색 가중치", ge=0.0, le=1.0),
    search_service: SearchService = Depends(get_search_service),
):
    """하이브리드 검색 (의미 검색 + 텍스트 검색)"""
    return search_service.hybrid_search(
        query=query,
        semantic_weight=semantic_weight,
        text_weight=text_weight,
        limit=limit
    )

# 의존성 주입을 위한 임시 함수 (실제로는 dependencies.py에 있어야 함)
def log_security_event(message: str, **kwargs):
    """Logs a security-related event."""
    log_message = f"[SECURITY] {message}"
    if kwargs:
        log_message += f" - Details: {kwargs}"
    app_logger.warning(log_message)
