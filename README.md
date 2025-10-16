# DevFlow ERP - Backend API

IT 스타트업을 위한 개발 워크플로우 관리 ERP 시스템의 백엔드 API입니다.

## 주요 기능

- **프로젝트 관리**: 프로젝트 생성, 수정, 조회
- **스프린트 관리**: 애자일 스프린트 계획 및 추적
- **이슈 트래킹**: 작업, 버그, 기능 요청 관리
- **팀 관리**: 팀 및 멤버십 관리
- **리소스 관리**: 서버 및 서비스 모니터링
- **배포 관리**: 배포 이력 추적 및 롤백

## 기술 스택

- **Language**: Python 3.13+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Authentication**: JWT + Authentik
- **Testing**: pytest
- **Logging**: loguru

## 빠른 시작

### 사전 요구사항

- Python 3.13+
- Docker & Docker Compose
- PostgreSQL 15+ (Docker 사용 시 불필요)
- Redis 7+ (Docker 사용 시 불필요)

### 1. 로컬 개발 환경 (Python 가상환경)

```bash
# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 설정값 입력

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker 개발 환경

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 설정값 입력

# 개발 환경 시작 (스크립트 사용)
./scripts/dev-start.sh

# 또는 직접 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 중지
docker-compose down
```

### 3. 프로덕션 배포

```bash
# 환경 변수 설정 (프로덕션용)
cp .env.example .env
# ENVIRONMENT=production으로 설정
# SECRET_KEY, 비밀번호 등 모든 값을 안전하게 변경

# 프로덕션 배포 (스크립트 사용)
./scripts/prod-deploy.sh

# 또는 직접 실행
docker build -f Dockerfile.prod -t devflow-erp-backend:latest .
docker-compose -f docker-compose.prod.yml up -d

# 상태 확인
curl http://localhost:8000/health

# 중지
docker-compose -f docker-compose.prod.yml down
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 프로젝트 구조

```
BE/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정 관리
│   ├── database.py          # DB 연결 설정
│   ├── dependencies.py      # 공통 의존성
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── api/v1/              # API 라우터
│   ├── crud/                # CRUD 로직
│   ├── core/                # 핵심 기능 (인증, 보안)
│   └── utils/               # 유틸리티
├── alembic/                 # DB 마이그레이션
├── tests/                   # 테스트 코드
├── scripts/                 # 배포 스크립트
├── logs/                    # 로그 파일
├── Dockerfile               # 개발용 Dockerfile
├── Dockerfile.prod          # 프로덕션 Dockerfile
├── docker-compose.yml       # 개발용 Compose
├── docker-compose.prod.yml  # 프로덕션 Compose
└── requirements.txt         # Python 의존성
```

## 환경 변수

주요 환경 변수 설정 (.env 파일):

```bash
# Application
APP_NAME=DevFlow ERP
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Authentik
AUTHENTIK_URL=http://localhost:9000
AUTHENTIK_TOKEN=your-token-here

# CORS
CORS_ORIGINS=http://localhost:3000
```

자세한 설정은 `.env.example` 파일을 참조하세요.

## 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 마이그레이션 이력 확인
alembic history
```

## 테스트

```bash
# 가상환경 활성화
source .venv/bin/activate

# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/api/v1/test_projects.py

# Coverage 리포트와 함께 실행
pytest --cov=app --cov-report=html
```

**테스트 결과**: 90/90 테스트 통과 (100%)

## 성능 최적화

### 데이터베이스 인덱스

42개의 데이터베이스 인덱스가 적용되어 있습니다:
- Foreign key 인덱스
- 자주 필터링되는 필드 인덱스
- 복합 인덱스 (날짜 범위, service+created_at)

마이그레이션: `alembic/versions/f14235f9eab8_add_performance_indexes.py`

### 로깅

- **개발 환경**: 컬러풀한 콘솔 출력 (DEBUG 레벨)
- **프로덕션 환경**:
  - 일별 로그 파일 로테이션
  - 일반 로그 30일 보관
  - 에러 로그 90일 보관
  - 자동 압축

## 보안

- JWT 기반 인증
- Authentik 연동
- CORS 설정
- 환경별 에러 메시지 분기 (프로덕션에서는 상세 오류 숨김)
- Non-root 사용자로 컨테이너 실행 (프로덕션)
- 입력값 검증 (Pydantic)
- SQL Injection 방지 (SQLAlchemy ORM)

## 모니터링

### Health Check 엔드포인트

- `GET /health`: 애플리케이션 상태 확인
- `GET /ready`: 준비 상태 확인 (DB 연결 등)

### 로그 확인

```bash
# Docker 환경
docker-compose logs -f backend

# 로컬 환경
tail -f logs/app_$(date +%Y-%m-%d).log
```

## 트러블슈팅

### 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
docker-compose exec postgres pg_isready -U devflow

# 연결 테스트
psql postgresql://devflow:password@localhost:5432/devflow_erp
```

### 마이그레이션 오류

```bash
# 마이그레이션 상태 확인
alembic current

# 강제로 특정 버전으로 설정
alembic stamp head
```

### 포트 충돌

.env 파일에서 포트 변경 또는 docker-compose.yml의 포트 매핑 수정

## 라이선스

MIT License

## 지원

- 이슈: https://github.com/yourusername/devflow-erp/issues
- 이메일: support@devflow.com
