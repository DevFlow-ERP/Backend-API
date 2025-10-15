from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from typing import Generator

from app.config import settings

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    echo=settings.DEBUG,  # SQL 쿼리 로깅 (디버그 모드에서만)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base 클래스 생성 (모든 모델이 상속받을 클래스) - SQLAlchemy 2.0 방식
class Base(DeclarativeBase):
    """
    모든 모델의 기본 클래스
    SQLAlchemy 2.0의 DeclarativeBase를 사용합니다.
    """
    pass


class TimestampMixin:
    """
    생성일시 및 수정일시를 자동으로 관리하는 Mixin 클래스
    """
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False,
        comment="생성일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정일시"
    )


def get_db() -> Generator:
    """
    데이터베이스 세션 의존성
    FastAPI의 Depends에서 사용됩니다.

    Yields:
        Session: 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    데이터베이스 초기화
    모든 테이블을 생성합니다.
    """
    Base.metadata.create_all(bind=engine)
