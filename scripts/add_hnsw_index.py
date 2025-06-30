import sqlalchemy

from app.models import SessionLocal


def main():
    """paper_chunks 테이블에 HNSW 인덱스를 생성합니다."""

    # 인덱스 생성 SQL (이미 존재하면 건너뛰기)
    # m, ef_construction 파라미터는 데이터 크기와 검색 요구사항에 따라 튜닝 가능
    create_index_sql = sqlalchemy.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_paper_chunks_embedding
        ON paper_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    db = SessionLocal()
    try:
        print("HNSW 인덱스를 생성합니다...")
        db.execute(create_index_sql)
        db.commit()
        print("✅ HNSW 인덱스가 성공적으로 생성되었거나 이미 존재합니다.")
    except Exception as e:
        print(f"🔥 인덱스 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
