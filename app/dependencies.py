"""
Common dependencies for FastAPI endpoints
FastAPI 엔드포인트에서 사용하는 공통 의존성
"""

from typing import Annotated, Generator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.auth import AuthentikClient
from app.core.exceptions import (
    AuthenticationError,
    UserInactiveError,
    UserNotFoundError,
)
from app.core.security import verify_token
from app.database import SessionLocal
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성

    Yields:
        Session: SQLAlchemy 데이터베이스 세션

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_authentik_client() -> AuthentikClient:
    """
    Authentik 클라이언트 의존성

    Returns:
        AuthentikClient: Authentik API 클라이언트
    """
    return AuthentikClient()


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    현재 로그인한 사용자 조회

    Args:
        authorization: Authorization 헤더 (Bearer {token})
        db: 데이터베이스 세션

    Returns:
        User: 현재 사용자 객체

    Raises:
        AuthenticationError: 인증 실패
        UserNotFoundError: 사용자를 찾을 수 없음
        UserInactiveError: 비활성화된 사용자

    Example:
        @app.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    if not authorization:
        raise AuthenticationError("Authorization header missing")

    # Bearer 토큰 추출
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("Invalid authentication scheme")
    except ValueError:
        raise AuthenticationError("Invalid authorization header format")

    # 토큰 검증
    payload = verify_token(token)
    user_id: int | None = payload.get("user_id")

    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)

    if not user.is_active:
        raise UserInactiveError()

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    현재 활성 사용자 조회 (get_current_user와 동일, 명시적 이름)

    Args:
        current_user: 현재 사용자

    Returns:
        User: 현재 활성 사용자

    Raises:
        UserInactiveError: 비활성화된 사용자
    """
    if not current_user.is_active:
        raise UserInactiveError()
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    현재 관리자 사용자 조회

    Args:
        current_user: 현재 사용자

    Returns:
        User: 관리자 사용자

    Raises:
        AuthorizationError: 관리자 권한 없음
    """
    if not current_user.is_admin:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Admin privileges required")
    return current_user


# Type aliases for easier use
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
DBSession = Annotated[Session, Depends(get_db)]
