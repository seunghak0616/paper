from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.server import app, get_db

# --- 테스트용 데이터베이스 설정 ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # 메모리 내장 DB 사용
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)


def override_get_db():
    """테스트 중 사용할 DB 세션을 제공하는 의존성 오버라이드 함수"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# API가 테스트 DB를 사용하도록 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# --- 테스트 케이스 ---

def test_health_check():
    """/health 엔드포인트가 정상적으로 200 OK와 status:ok를 반환하는지 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# TODO: /papers, /search, /papers/{title}/pdf 엔드포인트에 대한 테스트 케이스 추가
