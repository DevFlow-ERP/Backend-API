"""
Pagination utilities
페이지네이션 유틸리티 함수
"""

from typing import Generic, TypeVar
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.database import Base
from app.schemas.common import PaginatedResponse, PaginationMeta

T = TypeVar("T")
ModelType = TypeVar("ModelType", bound=Base)


def paginate(
    db: Session,
    query: Select,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple[list, PaginationMeta]:
    """
    SQLAlchemy 쿼리에 페이지네이션 적용

    Args:
        db: 데이터베이스 세션
        query: SQLAlchemy select 쿼리
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기
        max_page_size: 최대 페이지 크기

    Returns:
        tuple[list, PaginationMeta]: (항목 리스트, 페이지네이션 메타데이터)

    Example:
        >>> from sqlalchemy import select
        >>> query = select(User).where(User.is_active == True)
        >>> items, meta = paginate(db, query, page=1, page_size=20)
    """
    # 페이지 크기 제한
    if page_size > max_page_size:
        page_size = max_page_size

    # 페이지 번호 검증
    if page < 1:
        page = 1

    # 총 개수 조회
    total_count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_count_query).scalar() or 0

    # 페이지네이션 메타데이터 계산
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1

    # 쿼리에 offset, limit 적용
    skip = (page - 1) * page_size
    paginated_query = query.offset(skip).limit(page_size)

    # 결과 조회
    items = db.execute(paginated_query).scalars().all()

    # 메타데이터 생성
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

    return list(items), meta


def create_paginated_response(
    items: list[T],
    meta: PaginationMeta
) -> PaginatedResponse[T]:
    """
    페이지네이션 응답 생성

    Args:
        items: 항목 리스트
        meta: 페이지네이션 메타데이터

    Returns:
        PaginatedResponse[T]: 페이지네이션 응답 객체

    Example:
        >>> items, meta = paginate(db, query, page=1, page_size=20)
        >>> response = create_paginated_response(items, meta)
    """
    return PaginatedResponse(items=items, meta=meta)


def get_pagination_params(
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple[int, int]:
    """
    페이지네이션 파라미터 검증 및 반환

    Args:
        page: 페이지 번호
        page_size: 페이지 크기
        max_page_size: 최대 페이지 크기

    Returns:
        tuple[int, int]: (검증된 페이지, 검증된 페이지 크기)

    Example:
        >>> page, page_size = get_pagination_params(page=0, page_size=200)
        >>> # page=1, page_size=100 (max_page_size)
    """
    # 페이지 번호 검증
    if page < 1:
        page = 1

    # 페이지 크기 검증
    if page_size < 1:
        page_size = 20
    elif page_size > max_page_size:
        page_size = max_page_size

    return page, page_size


def calculate_skip_limit(
    page: int,
    page_size: int
) -> tuple[int, int]:
    """
    skip과 limit 값 계산

    Args:
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기

    Returns:
        tuple[int, int]: (skip, limit)

    Example:
        >>> skip, limit = calculate_skip_limit(page=3, page_size=20)
        >>> # skip=40, limit=20
    """
    skip = (page - 1) * page_size
    limit = page_size
    return skip, limit
