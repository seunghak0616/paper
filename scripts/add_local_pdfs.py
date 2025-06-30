from __future__ import annotations

import argparse
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from pathlib import Path

import openai
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from app.models import Paper, PaperChunk

# --- DB 연결 문제를 해결하기 위해 스크립트 최상단에서 환경 변수를 강제로 설정 ---
os.environ['DATABASE_URL'] = "postgresql://user:password@localhost:5432/papers"

# --- 설정 ---
BASE_DIR = Path(__file__).resolve().parent.parent
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


def process_pdf_and_embed(pdf_path: Path, db_session) -> None:
    """개별 PDF를 처리하고, 청크로 나누어 임베딩과 함께 DB에 저장"""
    if not pdf_path.exists():
        print(f"⚠️ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return

    # PDF 파일명에서 '.pdf' 확장자를 제거하여 제목으로 사용
    title = pdf_path.stem

    # 1. Paper 레코드 생성 또는 확인
    existing_paper = db_session.query(Paper).filter_by(title=title).first()
    if existing_paper:
        print(f"이미 처리된 논문입니다: {title}")
        return

    db_paper = Paper(
        title=title,
        pdf_path=str(pdf_path.resolve()),
    )
    db_session.add(db_paper)
    db_session.commit()
    db_session.refresh(db_paper)

    print(f"📄 '{db_paper.title}' 처리 중...")

    # 2. PDF 텍스트 추출
    try:
        reader = PdfReader(pdf_path)
        # 전체 페이지의 텍스트를 추출
        full_text = "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        print(f"🔥 PDF 텍스트 추출 실패: {pdf_path}, 오류: {e}")
        # 실패 시 롤백하고 다음 파일로 진행
        db_session.rollback()
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
                page_number=i // 5 + 1, # 임시 페이지 번호
            )
            db_session.add(db_chunk)

        db_session.commit()
        print("  - ✅ 임베딩 저장 완료")

    except Exception as e:
        print(f"🔥 임베딩 생성 또는 저장 실패: {e}")
        db_session.rollback()


def main(pdf_directory: str):
    """
    지정된 디렉토리의 모든 PDF 파일을 처리하고 DB에 저장합니다.
    """
    target_dir = Path(pdf_directory)
    if not target_dir.is_dir():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {pdf_directory}")
        return

    pdf_files = list(target_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"🤷 디렉토리에서 PDF 파일을 찾을 수 없습니다: {pdf_directory}")
        return

    print(f"총 {len(pdf_files)}개의 PDF 파일을 처리합니다.")

    # 이 스크립트에서만 사용할 DB 연결을 명시적으로 생성
    engine = create_engine(os.environ['DATABASE_URL'])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db_session = SessionLocal()
    try:
        with tqdm(total=len(pdf_files), desc="로컬 PDF 처리 중") as pbar:
            for pdf_path in pdf_files:
                process_pdf_and_embed(pdf_path, db_session)
                pbar.update(1)

        print("✅ 모든 논문 처리가 완료되었습니다.")

    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="지정된 디렉토리의 PDF 파일들을 처리하여 데이터베이스에 추가합니다.")
    parser.add_argument("directory", type=str, help="PDF 파일들이 있는 디렉토리 경로")
    args = parser.parse_args()

    main(args.directory)
