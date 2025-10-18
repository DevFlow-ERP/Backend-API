"""
FastAPI application entry point
DevFlow ERP 백엔드 애플리케이션
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.api.v1 import auth, dashboard, projects, sprints, issues, teams, members, servers, services, deployments
from app.config import settings
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## DevFlow ERP - IT 스타트업을 위한 개발 워크플로우 관리 ERP 시스템

### 주요 기능
* **프로젝트 관리**: 프로젝트 생성, 수정, 조회
* **스프린트 관리**: 애자일 스프린트 계획 및 추적
* **이슈 트래킹**: 작업, 버그, 기능 요청 관리
* **팀 관리**: 팀 및 멤버십 관리
* **리소스 관리**: 서버 및 서비스 모니터링
* **배포 관리**: 배포 이력 추적 및 롤백

### 인증
JWT 기반 인증을 사용합니다. `/api/v1/auth/token` 엔드포인트에서 토큰을 발급받아
`Authorization: Bearer <token>` 헤더에 포함하여 사용하세요.

### API 버전
현재 v1 API를 제공합니다. 모든 엔드포인트는 `/api/v1` 접두사를 사용합니다.
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "DevFlow ERP Team",
        "email": "support@devflow.com",
    },
    license_info={
        "name": "MIT License",
    },
    openapi_tags=[
        {"name": "Health", "description": "헬스 체크 및 시스템 상태"},
        {"name": "Authentication", "description": "인증 및 토큰 관리"},
        {"name": "Dashboard", "description": "대시보드 통계 및 요약 정보"},
        {"name": "Projects", "description": "프로젝트 관리"},
        {"name": "Sprints", "description": "스프린트 관리"},
        {"name": "Issues", "description": "이슈 트래킹"},
        {"name": "Teams", "description": "팀 관리"},
        {"name": "Members", "description": "멤버십 관리"},
        {"name": "Servers", "description": "서버 리소스 관리"},
        {"name": "Services", "description": "서비스 관리"},
        {"name": "Deployments", "description": "배포 이력 및 롤백"},
    ],
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Pydantic 검증 오류 핸들러
    요청 데이터 검증 실패 시 명확한 오류 메시지를 반환합니다.
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_detail["context"] = error["ctx"]
        errors.append(error_detail)

    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    SQLAlchemy 데이터베이스 오류 핸들러
    데이터베이스 관련 오류를 처리합니다.
    """
    logger.error(
        f"Database error on {request.method} {request.url.path}",
        exception=str(exc),
        exc_info=True,
    )

    # 프로덕션에서는 상세 오류를 숨김
    if settings.ENVIRONMENT == "production":
        detail = "A database error occurred"
    else:
        detail = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "type": "database_error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    일반 예외 핸들러
    처리되지 않은 모든 예외를 캐치합니다.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exception_type=type(exc).__name__,
        exception=str(exc),
        exc_info=True,
    )

    # 프로덕션에서는 상세 오류를 숨김
    if settings.ENVIRONMENT == "production":
        detail = "An internal server error occurred"
    else:
        detail = f"{type(exc).__name__}: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "type": "internal_error",
        },
    )


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"Shutting down {settings.APP_NAME}")


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
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
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
