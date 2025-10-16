"""
Authentik SSO integration
Authentik SSO 통합 로직
"""

from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthenticationError, InternalServerError
from app.models.user import User


class AuthentikClient:
    """
    Authentik API 클라이언트
    사용자 정보 조회 및 검증을 담당합니다.
    """

    def __init__(self):
        self.base_url = settings.AUTHENTIK_URL.rstrip("/")
        self.token = settings.AUTHENTIK_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_user_info(self, authentik_id: str) -> dict[str, Any]:
        """
        Authentik에서 사용자 정보 조회

        Args:
            authentik_id: Authentik 사용자 ID

        Returns:
            dict: 사용자 정보

        Raises:
            AuthenticationError: 사용자 정보 조회 실패
            InternalServerError: API 호출 실패
        """
        url = f"{self.base_url}/api/v3/core/users/{authentik_id}/"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 404:
                    raise AuthenticationError("User not found in Authentik")
                elif response.status_code != 200:
                    raise InternalServerError(
                        f"Authentik API error: {response.status_code}"
                    )

                return response.json()
        except httpx.RequestError as e:
            raise InternalServerError(f"Failed to connect to Authentik: {str(e)}")

    async def verify_user_token(self, token: str) -> dict[str, Any]:
        """
        Authentik 토큰 검증 및 사용자 정보 조회

        Args:
            token: Authentik 액세스 토큰

        Returns:
            dict: 사용자 정보

        Raises:
            AuthenticationError: 토큰 검증 실패
        """
        url = f"{self.base_url}/application/o/userinfo/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)

                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired token")
                elif response.status_code != 200:
                    raise InternalServerError(
                        f"Authentik API error: {response.status_code}"
                    )

                return response.json()
        except httpx.RequestError as e:
            raise InternalServerError(f"Failed to connect to Authentik: {str(e)}")


async def get_or_create_user_from_authentik(
    db: Session,
    authentik_id: str,
    email: str,
    username: str,
    is_admin: bool = False
) -> User:
    """
    Authentik 사용자 정보로부터 DB에 사용자 생성 또는 조회

    Args:
        db: 데이터베이스 세션
        authentik_id: Authentik 사용자 ID
        email: 이메일
        username: 사용자명
        is_admin: 관리자 여부

    Returns:
        User: 사용자 객체
    """
    # 기존 사용자 조회
    user = db.query(User).filter(User.authentik_id == authentik_id).first()

    if user:
        # 사용자 정보 업데이트
        user.email = email
        user.username = username
        db.commit()
        db.refresh(user)
        return user

    # 새 사용자 생성
    new_user = User(
        authentik_id=authentik_id,
        email=email,
        username=username,
        is_active=True,
        is_admin=is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def sync_user_from_authentik(
    db: Session,
    authentik_client: AuthentikClient,
    authentik_id: str
) -> User:
    """
    Authentik에서 사용자 정보를 동기화

    Args:
        db: 데이터베이스 세션
        authentik_client: Authentik 클라이언트
        authentik_id: Authentik 사용자 ID

    Returns:
        User: 동기화된 사용자 객체
    """
    # Authentik에서 사용자 정보 조회
    user_info = await authentik_client.get_user_info(authentik_id)

    # DB에 사용자 생성/업데이트
    user = await get_or_create_user_from_authentik(
        db=db,
        authentik_id=authentik_id,
        email=user_info.get("email", ""),
        username=user_info.get("username", ""),
        is_admin=user_info.get("is_superuser", False),
    )

    return user
