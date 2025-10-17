"""
Authentication API endpoints
인증 관련 API 엔드포인트
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    AuthentikClient,
    get_or_create_user_from_authentik,
)
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.dependencies import CurrentUser, get_authentik_client, get_db
from app.schemas.user import CurrentUserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    """토큰 요청 스키마"""
    authentik_token: str = Field(description="Authentik 액세스 토큰")


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(description="JWT 액세스 토큰")
    refresh_token: str = Field(description="JWT 리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(description="만료 시간 (초)")


class RefreshTokenRequest(BaseModel):
    """리프레시 토큰 요청 스키마"""
    refresh_token: str = Field(description="JWT 리프레시 토큰")


class DevLoginRequest(BaseModel):
    """개발용 로그인 요청 스키마 (Authentik 없이 이메일로 로그인)"""
    email: str = Field(description="사용자 이메일")
    password: str = Field(default="devpassword", description="개발용 비밀번호 (기본값: devpassword)")


@router.post("/token", response_model=TokenResponse)
async def login(
    request: TokenRequest,
    db: Session = Depends(get_db),
    authentik_client: AuthentikClient = Depends(get_authentik_client),
) -> TokenResponse:
    """
    Authentik 토큰으로 로그인하여 JWT 토큰 발급

    이 엔드포인트는 Authentik에서 발급한 토큰을 검증하고,
    사용자 정보를 DB에 동기화한 후 JWT 토큰을 발급합니다.

    Args:
        request: Authentik 토큰 요청
        db: 데이터베이스 세션
        authentik_client: Authentik 클라이언트

    Returns:
        TokenResponse: JWT 액세스 토큰 및 리프레시 토큰

    Raises:
        AuthenticationError: 인증 실패

    Example:
        POST /api/v1/auth/token
        {
            "authentik_token": "eyJhbGciOiJSUzI1NiIs..."
        }
    """
    # Authentik 토큰 검증 및 사용자 정보 조회
    try:
        user_info = await authentik_client.verify_user_token(request.authentik_token)
    except Exception as e:
        raise AuthenticationError(f"Failed to verify Authentik token: {str(e)}")

    # 사용자 정보 추출
    authentik_id = user_info.get("sub")
    email = user_info.get("email")
    username = user_info.get("preferred_username") or user_info.get("name")
    is_superuser = user_info.get("is_superuser", False)

    if not authentik_id or not email or not username:
        raise AuthenticationError("Invalid user info from Authentik")

    # DB에 사용자 생성 또는 업데이트
    user = await get_or_create_user_from_authentik(
        db=db,
        authentik_id=authentik_id,
        email=email,
        username=username,
        is_admin=is_superuser,
    )

    # JWT 토큰 생성
    from app.config import settings

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    리프레시 토큰으로 새로운 액세스 토큰 발급

    Args:
        request: 리프레시 토큰 요청
        db: 데이터베이스 세션

    Returns:
        TokenResponse: 새로운 JWT 액세스 토큰

    Raises:
        AuthenticationError: 리프레시 토큰 검증 실패

    Example:
        POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }
    """
    # 리프레시 토큰 검증
    try:
        payload = verify_token(request.refresh_token)
    except Exception:
        raise AuthenticationError("Invalid refresh token")

    # 토큰 타입 확인
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    # 사용자 존재 확인
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User is inactive")

    # 새로운 액세스 토큰 생성
    from app.config import settings

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def dev_login(
    request: DevLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    개발 환경용 간단한 이메일 로그인 (Authentik 없이)

    ⚠️ 주의: 이 엔드포인트는 개발 환경에서만 사용하세요!
    프로덕션에서는 Authentik 기반 인증을 사용해야 합니다.

    Args:
        request: 이메일 로그인 요청
        db: 데이터베이스 세션

    Returns:
        TokenResponse: JWT 액세스 토큰 및 리프레시 토큰

    Example:
        POST /api/v1/auth/login
        {
            "email": "admin@devflow.com",
            "password": "devpassword"
        }
    """
    from app.models.user import User

    # 이메일로 사용자 조회
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise AuthenticationError("사용자를 찾을 수 없습니다")

    if not user.is_active:
        raise AuthenticationError("비활성화된 사용자입니다")

    # 개발 환경에서는 비밀번호 체크를 간단하게 처리
    # 프로덕션에서는 반드시 실제 비밀번호 검증을 구현해야 함
    if request.password != "devpassword":
        raise AuthenticationError("잘못된 비밀번호입니다")

    # JWT 토큰 생성
    from app.config import settings

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/verify")
async def verify_token_endpoint(
    current_user: CurrentUser,
) -> dict:
    """
    토큰 유효성 검증

    Args:
        current_user: 현재 로그인한 사용자

    Returns:
        dict: 검증 결과
    """
    return {"valid": True, "user_id": current_user.id}


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> CurrentUserResponse:
    """
    현재 로그인한 사용자 정보 조회

    Args:
        current_user: 현재 로그인한 사용자

    Returns:
        CurrentUserResponse: 사용자 정보

    Example:
        GET /api/v1/auth/me
        Headers: Authorization: Bearer {token}
    """
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        authentik_id=current_user.authentik_id,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat(),
    )
