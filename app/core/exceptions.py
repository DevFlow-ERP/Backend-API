"""
Custom exceptions for the application
애플리케이션에서 사용하는 커스텀 예외를 정의합니다.
"""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """인증 실패 예외"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """권한 부족 예외"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundError(HTTPException):
    """리소스를 찾을 수 없는 예외"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class BadRequestError(HTTPException):
    """잘못된 요청 예외"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ConflictError(HTTPException):
    """중복 리소스 예외"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class InternalServerError(HTTPException):
    """서버 내부 오류 예외"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class TokenExpiredError(AuthenticationError):
    """토큰 만료 예외"""
    def __init__(self):
        super().__init__(detail="Token has expired")


class InvalidTokenError(AuthenticationError):
    """유효하지 않은 토큰 예외"""
    def __init__(self):
        super().__init__(detail="Invalid token")


class UserNotFoundError(NotFoundError):
    """사용자를 찾을 수 없는 예외"""
    def __init__(self, user_id: int | str | None = None):
        detail = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(detail=detail)


class UserInactiveError(AuthenticationError):
    """비활성화된 사용자 예외"""
    def __init__(self):
        super().__init__(detail="User is inactive")


class ProjectNotFoundError(NotFoundError):
    """프로젝트를 찾을 수 없는 예외"""
    def __init__(self, project_id: int | None = None):
        detail = f"Project {project_id} not found" if project_id else "Project not found"
        super().__init__(detail=detail)


class TeamNotFoundError(NotFoundError):
    """팀을 찾을 수 없는 예외"""
    def __init__(self, team_id: int | None = None):
        detail = f"Team {team_id} not found" if team_id else "Team not found"
        super().__init__(detail=detail)


class InsufficientTeamPermissionsError(AuthorizationError):
    """팀 권한 부족 예외"""
    def __init__(self, required_role: str | None = None):
        detail = f"Requires {required_role} role" if required_role else "Insufficient team permissions"
        super().__init__(detail=detail)
