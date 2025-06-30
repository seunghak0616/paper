from __future__ import annotations

import json
from pathlib import Path

import openai
from pypdf import PdfReader
from tqdm import tqdm

from app.models import Paper, PaperChunk, SessionLocal

# --- 설정 ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
META_PATH = DATA_DIR / "metadata.json"
# OpenAI 클라이언트는 .env 파일의 OPENAI_API_KEY를 자동으로 읽음
client = openai.OpenAI()
CHUNK_SIZE = 500  # 텍스트를 나눌 글자 수 기준
EMBEDDING_MODEL = "text-embedding-ada-002"


def split_text_into_chunks(text: str, chunk_size: int) -> list[str]:
    """긴 텍스트를 지정된 크기의 청크로 분할합니다."""
    if not text:
        return []

    # 먼저 문단으로 나누고, 너무 긴 문단은 문장으로 나눕니다.
    chunks = []
    paragraphs = text.split("\n\n")
    for p in paragraphs:
        if len(p) <= chunk_size:
            chunks.append(p.strip())
        else:
            sentences = p.split(". ")
            current_chunk = ""
            for s in sentences:
                if len(current_chunk) + len(s) + 1 > chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = s + ". "
                else:
                    current_chunk += s + ". "
            if current_chunk:
                chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


def process_pdf_and_embed(paper_meta: dict, db_session) -> None:
    """개별 PDF를 처리하고, 청크로 나누어 임베딩과 함께 DB에 저장"""
    pdf_path = PDF_DIR / (paper_meta["file_name"])
    if not pdf_path.exists():
        print(f"⚠️ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return

    # 1. Paper 레코드 생성
    db_paper = Paper(
        title=paper_meta["title"],
        author=paper_meta.get("author"),
        publisher=paper_meta.get("publisher"),
        # TODO: 날짜 형식 파싱 필요
        # published_date=paper_meta.get("published_date"),
        abstract=paper_meta.get("abstract"),
        pdf_path=str(pdf_path),
    )
    db_session.add(db_paper)
    db_session.commit()
    db_session.refresh(db_paper)

    print(f"📄 '{db_paper.title}' 처리 중...")

    # 2. PDF 텍스트 추출
    try:
        reader = PdfReader(pdf_path)
        full_text = "\n".join([page.extract_text() for i, page in enumerate(reader.pages) if i < 5]) # 테스트를 위해 5페이지만
    except Exception as e:
        print(f"🔥 PDF 텍스트 추출 실패: {pdf_path}, 오류: {e}")
        return

    # 3. 텍스트 청킹
    chunks = split_text_into_chunks(full_text, CHUNK_SIZE)
    if not chunks:
        print(f"ℹ️ 텍스트를 청크로 나눌 수 없습니다: {pdf_path}")
        return

    print(f"  - {len(chunks)}개의 청크로 분할됨")

    # 4. 각 청크 임베딩 생성 및 저장
    try:
        # 한 번에 여러 청크를 처리하여 API 호출 최소화
        response = client.embeddings.create(input=chunks, model=EMBEDDING_MODEL)
        embeddings = [item.embedding for item in response.data]

        for i, chunk_text in enumerate(chunks):
            db_chunk = PaperChunk(
                paper_id=db_paper.id,
                chunk_text=chunk_text,
                embedding=embeddings[i],
                # TODO: 정확한 페이지 번호 추적 기능 추가
                page_number=i // 5 + 1, # 임시 페이지 번호
            )
            db_session.add(db_chunk)

        db_session.commit()
        print("  - ✅ 임베딩 저장 완료")

    except Exception as e:
        print(f"🔥 임베딩 생성 또는 저장 실패: {e}")
        db_session.rollback()


def main():
    """
    metadata.json을 읽어 모든 논문 데이터를 처리하고 DB에 저장합니다.
    """
    if not META_PATH.exists():
        print("❌ metadata.json 파일을 찾을 수 없습니다. 크롤러를 먼저 실행하세요.")
        return

    papers_meta = json.loads(META_PATH.read_text("utf-8"))

    db_session = SessionLocal()
    try:
        with tqdm(total=len(papers_meta), desc="논문 처리 중") as pbar:
            for paper_meta in papers_meta:
                # 이미 처리된 논문인지 확인
                existing_paper = db_session.query(Paper).filter_by(title=paper_meta["title"]).first()
                if existing_paper:
                    print(f"이미 처리된 논문입니다: {paper_meta['title']}")
                    pbar.update(1)
                    continue

                process_pdf_and_embed(paper_meta, db_session)
                pbar.update(1)

        print("✅ 모든 논문 처리가 완료되었습니다.")

    finally:
        db_session.close()


if __name__ == "__main__":
    main()
