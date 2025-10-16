"""
Filter and Sort utilities
필터링 및 정렬 유틸리티 함수
"""

from typing import Any, Optional
from enum import Enum

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from app.database import Base


class SortOrder(str, Enum):
    """정렬 순서"""
    ASC = "asc"
    DESC = "desc"


def apply_filters(
    query: Select | Query,
    model: type[Base],
    filters: dict[str, Any]
) -> Select | Query:
    """
    쿼리에 필터 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        filters: 필터 딕셔너리 {필드명: 값}

    Returns:
        Select | Query: 필터가 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(User)
        >>> filters = {"is_active": True, "is_admin": False}
        >>> query = apply_filters(query, User, filters)
    """
    for field, value in filters.items():
        if value is not None and hasattr(model, field):
            column = getattr(model, field)
            query = query.where(column == value)
    return query


def apply_search(
    query: Select | Query,
    model: type[Base],
    search_fields: list[str],
    search_term: str | None
) -> Select | Query:
    """
    쿼리에 검색 조건 적용 (부분 일치)

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        search_fields: 검색할 필드 목록
        search_term: 검색어

    Returns:
        Select | Query: 검색 조건이 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(User)
        >>> query = apply_search(query, User, ["username", "email"], "john")
    """
    if not search_term or not search_fields:
        return query

    # OR 조건으로 여러 필드 검색
    conditions = []
    for field in search_fields:
        if hasattr(model, field):
            column = getattr(model, field)
            conditions.append(column.ilike(f"%{search_term}%"))

    if conditions:
        from sqlalchemy import or_
        query = query.where(or_(*conditions))

    return query


def apply_sort(
    query: Select | Query,
    model: type[Base],
    sort_by: str | None = None,
    order: SortOrder | str = SortOrder.ASC
) -> Select | Query:
    """
    쿼리에 정렬 조건 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        sort_by: 정렬 필드명
        order: 정렬 순서 (asc 또는 desc)

    Returns:
        Select | Query: 정렬이 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(User)
        >>> query = apply_sort(query, User, "created_at", SortOrder.DESC)
    """
    if not sort_by or not hasattr(model, sort_by):
        return query

    column = getattr(model, sort_by)

    # 문자열을 SortOrder로 변환
    if isinstance(order, str):
        order = SortOrder(order.lower())

    if order == SortOrder.DESC:
        query = query.order_by(desc(column))
    else:
        query = query.order_by(asc(column))

    return query


def apply_range_filter(
    query: Select | Query,
    model: type[Base],
    field: str,
    min_value: Any | None = None,
    max_value: Any | None = None
) -> Select | Query:
    """
    쿼리에 범위 필터 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        field: 필드명
        min_value: 최소값
        max_value: 최대값

    Returns:
        Select | Query: 범위 필터가 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(Issue)
        >>> query = apply_range_filter(query, Issue, "estimate_hours", min_value=1, max_value=10)
    """
    if not hasattr(model, field):
        return query

    column = getattr(model, field)

    if min_value is not None:
        query = query.where(column >= min_value)

    if max_value is not None:
        query = query.where(column <= max_value)

    return query


def apply_date_range_filter(
    query: Select | Query,
    model: type[Base],
    field: str,
    start_date: Any | None = None,
    end_date: Any | None = None
) -> Select | Query:
    """
    쿼리에 날짜 범위 필터 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        field: 날짜 필드명
        start_date: 시작일
        end_date: 종료일

    Returns:
        Select | Query: 날짜 범위 필터가 적용된 쿼리

    Example:
        >>> from datetime import date
        >>> from sqlalchemy import select
        >>> query = select(Sprint)
        >>> query = apply_date_range_filter(
        ...     query, Sprint, "start_date",
        ...     start_date=date(2025, 1, 1),
        ...     end_date=date(2025, 12, 31)
        ... )
    """
    return apply_range_filter(query, model, field, start_date, end_date)


def apply_in_filter(
    query: Select | Query,
    model: type[Base],
    field: str,
    values: list[Any] | None = None
) -> Select | Query:
    """
    쿼리에 IN 필터 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        field: 필드명
        values: 값 리스트

    Returns:
        Select | Query: IN 필터가 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(Issue)
        >>> query = apply_in_filter(query, Issue, "status", ["TODO", "IN_PROGRESS"])
    """
    if not values or not hasattr(model, field):
        return query

    column = getattr(model, field)
    query = query.where(column.in_(values))

    return query


def apply_null_filter(
    query: Select | Query,
    model: type[Base],
    field: str,
    is_null: bool = True
) -> Select | Query:
    """
    쿼리에 NULL 필터 적용

    Args:
        query: SQLAlchemy 쿼리
        model: 모델 클래스
        field: 필드명
        is_null: True면 IS NULL, False면 IS NOT NULL

    Returns:
        Select | Query: NULL 필터가 적용된 쿼리

    Example:
        >>> from sqlalchemy import select
        >>> query = select(Issue)
        >>> query = apply_null_filter(query, Issue, "assignee_id", is_null=True)
    """
    if not hasattr(model, field):
        return query

    column = getattr(model, field)

    if is_null:
        query = query.where(column.is_(None))
    else:
        query = query.where(column.isnot(None))

    return query


class QueryBuilder:
    """
    쿼리 빌더 클래스

    메서드 체이닝을 통해 필터와 정렬을 쉽게 적용할 수 있습니다.

    Example:
        >>> from sqlalchemy import select
        >>> builder = QueryBuilder(select(User), User)
        >>> query = (builder
        ...     .filter(is_active=True)
        ...     .search(["username", "email"], "john")
        ...     .sort("created_at", SortOrder.DESC)
        ...     .build())
    """

    def __init__(self, query: Select | Query, model: type[Base]):
        """
        쿼리 빌더 초기화

        Args:
            query: 기본 쿼리
            model: 모델 클래스
        """
        self.query = query
        self.model = model

    def filter(self, **kwargs: Any) -> "QueryBuilder":
        """필터 적용"""
        self.query = apply_filters(self.query, self.model, kwargs)
        return self

    def search(
        self,
        search_fields: list[str],
        search_term: str | None
    ) -> "QueryBuilder":
        """검색 조건 적용"""
        self.query = apply_search(self.query, self.model, search_fields, search_term)
        return self

    def sort(
        self,
        sort_by: str | None = None,
        order: SortOrder | str = SortOrder.ASC
    ) -> "QueryBuilder":
        """정렬 조건 적용"""
        self.query = apply_sort(self.query, self.model, sort_by, order)
        return self

    def range(
        self,
        field: str,
        min_value: Any | None = None,
        max_value: Any | None = None
    ) -> "QueryBuilder":
        """범위 필터 적용"""
        self.query = apply_range_filter(
            self.query,
            self.model,
            field,
            min_value,
            max_value
        )
        return self

    def date_range(
        self,
        field: str,
        start_date: Any | None = None,
        end_date: Any | None = None
    ) -> "QueryBuilder":
        """날짜 범위 필터 적용"""
        self.query = apply_date_range_filter(
            self.query,
            self.model,
            field,
            start_date,
            end_date
        )
        return self

    def in_filter(
        self,
        field: str,
        values: list[Any] | None = None
    ) -> "QueryBuilder":
        """IN 필터 적용"""
        self.query = apply_in_filter(self.query, self.model, field, values)
        return self

    def null_filter(
        self,
        field: str,
        is_null: bool = True
    ) -> "QueryBuilder":
        """NULL 필터 적용"""
        self.query = apply_null_filter(self.query, self.model, field, is_null)
        return self

    def build(self) -> Select | Query:
        """최종 쿼리 반환"""
        return self.query
