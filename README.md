# 📚 Papers API - AI-Powered Academic Paper Search System

> **엔터프라이즈급 학술 논문 크롤링 및 AI 검색 플랫폼**

DBpia Open API를 통한 논문 수집과 OpenAI 임베딩 기반 의미 검색을 제공하는 차세대 학술 연구 플랫폼입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org)

## ✨ 주요 특징

### 🔍 **AI 기반 검색**
- **의미 검색**: OpenAI 임베딩을 활용한 자연어 쿼리 지원
- **하이브리드 검색**: 의미 검색 + 전문 검색 결합
- **HNSW 인덱스**: PostgreSQL pgvector로 고성능 벡터 검색
- **실시간 자동완성**: 검색어 제안 기능

### 🏗️ **엔터프라이즈 아키텍처**
- **3-Tier 구조**: Repository/Service/Controller 패턴
- **타입 안전성**: 100% 타입 힌트 및 Pydantic 스키마
- **보안 강화**: CORS, 환경변수 검증, 감사 로깅
- **확장 가능**: 마이크로서비스 아키텍처 준비

### 🚀 **개발자 경험**
- **Poetry**: 현대적 의존성 관리
- **Pre-commit**: 자동화된 코드 품질 검사
- **Structured Logging**: JSON 기반 구조화된 로깅
- **Comprehensive Testing**: 단위/통합/E2E 테스트

---

## 🚀 빠른 시작

### Poetry를 사용한 설치 (권장)
```bash
# 1) 저장소 클론
git clone https://github.com/seunghak0616/paper.git
cd paper

# 2) Poetry로 의존성 설치
poetry install

# 3) 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 설정

# 4) 데이터베이스 초기화
make db-init

# 5) 개발 서버 시작
make run
```

### 기존 pip 방식
```bash
# 1) 가상환경 생성
python -m venv venv && source venv/bin/activate

# 2) 의존성 설치
pip install -r requirements.txt

# 3) 서버 실행
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose 사용
```bash
# 모든 서비스 (API + PostgreSQL) 실행
docker-compose up -d

# 개발 모드
docker-compose -f docker-compose.dev.yml up
```

### 📡 API 접속
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🔧 환경 변수

`.env` 파일에 다음 변수들을 설정하세요:

```bash
# 환경 설정
ENVIRONMENT=development  # development, staging, production

# 데이터베이스
DATABASE_URL=postgresql://postgres:password@localhost:5432/papers

# API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here
DBPIA_API_KEY=your-dbpia-api-key-here

# CORS 설정
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# 서버 설정
HOST=0.0.0.0
PORT=8000
```

---

## 📚 API 문서

### 🔍 검색 엔드포인트

#### 의미 검색
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "딥러닝을 활용한 자연어 처리"}'
```

#### 하이브리드 검색
```bash
curl -X POST "http://localhost:8000/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{"query": "머신러닝", "semantic_weight": 0.7, "text_weight": 0.3}'
```

#### 자동완성
```bash
curl "http://localhost:8000/search/suggestions?q=딥러"
```

### 📄 논문 관리

#### 논문 목록
```bash
curl "http://localhost:8000/papers?skip=0&limit=10&q=검색어"
```

#### 논문 통계
```bash
curl "http://localhost:8000/papers/stats"
```

#### 저자별 논문
```bash
curl "http://localhost:8000/papers/author/김철수"
```

### 📁 PDF 서빙
```bash
curl "http://localhost:8000/papers/{논문제목}/pdf"
```

---

## 🛠️ 개발 가이드

### Makefile 명령어

```bash
# 개발 환경 설정
make setup              # 전체 설정 (의존성 + 환경변수 + DB)
make dev               # 개발 의존성 설치
make env-example       # .env 파일 생성

# 코드 품질
make lint              # 린팅 검사
make format            # 코드 포맷팅
make security          # 보안 검사
make ci                # 모든 검사 실행

# 테스트
make test              # 전체 테스트
make test-unit         # 단위 테스트
make test-integration  # 통합 테스트
make test-cov          # 커버리지 포함

# 서버 실행
make run               # 개발 서버
make run-prod          # 프로덕션 서버

# 데이터 관리
make crawl             # 크롤러 실행
make etl               # ETL 파이프라인
make add-index         # HNSW 인덱스 생성
make tune-hnsw         # HNSW 파라미터 튜닝

# 정리
make clean             # 빌드 아티팩트 정리
make clean-data        # 데이터 파일 정리
```

### 프로젝트 구조

```
paper/
├── app/                    # 메인 애플리케이션
│   ├── core/              # 핵심 컴포넌트 (로깅 등)
│   ├── models.py          # SQLAlchemy 모델
│   ├── schemas.py         # Pydantic 스키마
│   ├── server.py          # FastAPI 애플리케이션
│   ├── config.py          # 설정 관리
│   ├── exceptions.py      # 커스텀 예외
│   ├── dependencies.py    # 의존성 주입
│   ├── repositories/      # 데이터 접근 계층
│   └── services/          # 비즈니스 로직 계층
├── crawler/               # 크롤링 모듈
├── scripts/               # ETL 및 유틸리티
├── frontend/              # 웹 프론트엔드
├── tests/                 # 테스트 코드
│   ├── unit/             # 단위 테스트
│   ├── integration/      # 통합 테스트
│   └── fixtures/         # 테스트 데이터
├── data/                  # 데이터 파일
├── downloaded_pdfs/       # 다운로드된 PDF 파일
├── pyproject.toml         # Poetry 설정
├── Makefile              # 개발 워크플로우
└── docker-compose.yml    # Docker 설정
```

---

## 🧪 테스트

### 테스트 실행
```bash
# 모든 테스트
poetry run pytest

# 커버리지 포함
poetry run pytest --cov=app --cov-report=html

# 특정 테스트만
poetry run pytest tests/unit/test_services.py

# 마커 기반
poetry run pytest -m "not slow"
```

### 테스트 작성 가이드

```python
# tests/unit/test_example.py
import pytest
from app.services import PaperService

def test_paper_service_get_papers(test_db_session):
    """Test paper service functionality."""
    service = PaperService(test_db_session)
    papers = service.get_papers(limit=10)
    assert len(papers) <= 10
```

---

## 📊 모니터링 및 로깅

### 구조화된 로깅

시스템은 JSON 형태의 구조화된 로그를 생성합니다:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Search completed",
  "module": "app.services.search_service",
  "log_type": "business",
  "query": "딥러닝",
  "results_count": 42,
  "duration_ms": 156.7
}
```

### 로그 파일

```
logs/
├── app.log        # 일반 애플리케이션 로그
├── error.log      # 에러 로그
├── access.log     # HTTP 접근 로그
└── audit.log      # 보안 감사 로그
```

---

## 🚢 배포

### 프로덕션 체크리스트

- [ ] 환경변수 설정 (`ENVIRONMENT=production`)
- [ ] CORS 도메인 명시적 설정
- [ ] 데이터베이스 백업 설정
- [ ] 모니터링 도구 연동
- [ ] SSL 인증서 설정
- [ ] 로드 밸런서 구성

### Docker 배포

```bash
# 이미지 빌드
docker build -t paper-api:latest .

# 프로덕션 실행
docker-compose -f docker-compose.prod.yml up -d
```

### 환경별 설정

```bash
# 개발
export ENVIRONMENT=development

# 스테이징
export ENVIRONMENT=staging
export CORS_ORIGINS=https://staging.yourdomain.com

# 프로덕션
export ENVIRONMENT=production
export CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 🤝 기여 가이드

### 개발 워크플로우

1. **Fork** 후 feature 브랜치 생성
2. **개발** 및 테스트 작성
3. **Pre-commit 훅** 실행: `pre-commit run --all-files`
4. **테스트** 실행: `make test`
5. **Pull Request** 생성

### 코드 스타일

- **Python**: Black, isort, ruff
- **Docstring**: Google 스타일
- **타입 힌트**: 모든 함수에 적용
- **테스트**: pytest, 최소 80% 커버리지

---

## 📈 성능

### 벤치마크 결과

- **검색 응답시간**: 평균 150ms
- **동시 사용자**: 1000+ 지원
- **벡터 검색**: HNSW 인덱스로 sub-second 응답
- **메모리 사용량**: 512MB 미만

### 최적화 팁

```python
# 배치 검색으로 성능 향상
results = search_service.batch_search([
    "쿼리1", "쿼리2", "쿼리3"
])

# 캐싱 활용
@lru_cache(maxsize=1000)
def cached_search(query: str):
    return search_service.semantic_search(query)
```

---

## 🔒 보안

### 보안 기능

- ✅ **CORS 제한**: 환경별 도메인 화이트리스트
- ✅ **Rate Limiting**: slowapi로 요청 제한
- ✅ **입력 검증**: Pydantic으로 타입 안전성
- ✅ **SQL Injection 방지**: ORM 사용
- ✅ **감사 로깅**: 보안 이벤트 추적

### 보안 검사

```bash
# 취약점 스캔
make security

# 의존성 보안 검사
poetry run safety check

# 코드 보안 검사
poetry run bandit -r app/
```

---

## 📞 지원

### 문서
- **API 문서**: `/docs` (Swagger UI)
- **기술 문서**: `/redoc` (ReDoc)

### 이슈 리포팅
GitHub Issues를 통해 버그 리포트나 기능 요청을 해주세요.

### 라이선스
MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 확인하세요.

---

## 🏆 Contributors

이 프로젝트는 다음 기술들로 구축되었습니다:

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI/ML**: OpenAI, pgvector, HNSW
- **DevOps**: Docker, Poetry, GitHub Actions
- **Testing**: pytest, Playwright
- **Monitoring**: Loguru, Structured Logging

---

<p align="center">
  <strong>⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!</strong>
</p>