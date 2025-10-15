from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import get_db, engine
from sqlalchemy import text


# Lifespan 컨텍스트 매니저 (startup/shutdown 이벤트 처리)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작 및 종료 시 실행되는 로직
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="IT 스타트업을 위한 개발 워크플로우 관리 ERP 시스템",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check 엔드포인트
@app.get("/health", tags=["System"])
async def health_check():
    """
    헬스 체크 엔드포인트
    시스템이 정상 동작하는지 확인합니다.
    """
    return {"status": "ok"}


@app.get("/ready", tags=["System"])
async def readiness_check():
    """
    레디니스 체크 엔드포인트
    데이터베이스 연결을 포함한 시스템 준비 상태를 확인합니다.
    """
    try:
        # 데이터베이스 연결 테스트
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }


# Root 엔드포인트
@app.get("/", tags=["System"])
async def root():
    """
    루트 엔드포인트
    API 정보를 반환합니다.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


# API 라우터를 여기에 추가할 예정
# app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
# app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
