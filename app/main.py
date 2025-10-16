"""
FastAPI application entry point
DevFlow ERP 백엔드 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, projects, sprints, issues, teams, members, servers, services, deployments
from app.config import settings

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DevFlow ERP - IT 스타트업을 위한 개발 워크플로우 관리 ERP 시스템",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    헬스 체크 엔드포인트
    애플리케이션이 정상 동작 중인지 확인합니다.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    준비 상태 체크 엔드포인트
    애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다.
    """
    # TODO: 데이터베이스 연결 확인 등 추가
    return {
        "status": "ready",
        "database": "connected",  # 실제 DB 연결 확인 로직 필요
    }


# API 라우터 등록
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(sprints.router, prefix="/api/v1")
app.include_router(issues.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(servers.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False,
    )
