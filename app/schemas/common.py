"""
Common Pydantic schemas
공통으로 사용되는 스키마를 정의합니다.
"""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field, ConfigDict


# Generic type for paginated responses
T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    페이지네이션 파라미터
    쿼리 파라미터로 사용됩니다.
    """
    page: int = Field(default=1, ge=1, description="페이지 번호 (1부터 시작)")
    page_size: int = Field(default=20, ge=1, le=100, description="페이지당 항목 수 (최대 100)")

    @property
    def skip(self) -> int:
        """데이터베이스 쿼리에서 건너뛸 항목 수"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """데이터베이스 쿼리에서 가져올 항목 수"""
        return self.page_size


class PaginationMeta(BaseModel):
    """
    페이지네이션 메타데이터
    """
    total: int = Field(description="전체 항목 수")
    page: int = Field(description="현재 페이지")
    page_size: int = Field(description="페이지당 항목 수")
    total_pages: int = Field(description="전체 페이지 수")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    페이지네이션 응답
    Generic 타입을 사용하여 다양한 타입의 리스트를 담을 수 있습니다.
    """
    items: list[T] = Field(description="항목 리스트")
    meta: PaginationMeta = Field(description="페이지네이션 메타데이터")

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """
    에러 상세 정보
    """
    field: Optional[str] = Field(default=None, description="에러가 발생한 필드")
    message: str = Field(description="에러 메시지")
    code: Optional[str] = Field(default=None, description="에러 코드")


class ErrorResponse(BaseModel):
    """
    에러 응답
    API 에러 발생 시 반환됩니다.
    """
    error: str = Field(description="에러 타입")
    message: str = Field(description="에러 메시지")
    details: Optional[list[ErrorDetail]] = Field(default=None, description="상세 에러 정보")


class SuccessResponse(BaseModel):
    """
    성공 응답
    간단한 성공 메시지를 반환할 때 사용합니다.
    """
    success: bool = Field(default=True, description="성공 여부")
    message: str = Field(description="성공 메시지")


class TimestampSchema(BaseModel):
    """
    타임스탬프 스키마
    created_at, updated_at 필드를 포함하는 기본 스키마입니다.
    """
    created_at: str = Field(description="생성일시 (ISO 8601)")
    updated_at: str = Field(description="수정일시 (ISO 8601)")

    model_config = ConfigDict(from_attributes=True)
