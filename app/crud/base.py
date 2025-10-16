"""
Base CRUD operations
제네릭 타입을 사용한 기본 CRUD 클래스
"""

from typing import Any, Generic, TypeVar, Type

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import Base

# Type variables for generic CRUD
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    기본 CRUD 클래스

    모든 CRUD 작업에 대한 기본 메서드를 제공합니다.
    제네릭 타입을 사용하여 타입 안전성을 보장합니다.

    Type Parameters:
        ModelType: SQLAlchemy 모델 타입
        CreateSchemaType: 생성용 Pydantic 스키마
        UpdateSchemaType: 수정용 Pydantic 스키마

    Example:
        class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
            pass
    """

    def __init__(self, model: Type[ModelType]):
        """
        CRUD 객체 초기화

        Args:
            model: SQLAlchemy 모델 클래스
        """
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """
        ID로 단일 레코드 조회

        Args:
            db: 데이터베이스 세션
            id: 조회할 레코드의 ID

        Returns:
            ModelType | None: 조회된 레코드 또는 None

        Example:
            user = crud_user.get(db, user_id=1)
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """
        여러 레코드 조회 (페이지네이션)

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[ModelType]: 조회된 레코드 리스트

        Example:
            users = crud_user.get_multi(db, skip=0, limit=20)
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        새 레코드 생성

        Args:
            db: 데이터베이스 세션
            obj_in: 생성할 데이터 (Pydantic 스키마)

        Returns:
            ModelType: 생성된 레코드

        Example:
            user = crud_user.create(db, obj_in=UserCreate(email="user@example.com"))
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        레코드 수정

        Args:
            db: 데이터베이스 세션
            db_obj: 수정할 DB 객체
            obj_in: 수정할 데이터 (Pydantic 스키마 또는 dict)

        Returns:
            ModelType: 수정된 레코드

        Example:
            user = crud_user.update(db, db_obj=user, obj_in=UserUpdate(email="new@example.com"))
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType | None:
        """
        레코드 삭제

        Args:
            db: 데이터베이스 세션
            id: 삭제할 레코드의 ID

        Returns:
            ModelType | None: 삭제된 레코드 또는 None

        Example:
            deleted_user = crud_user.delete(db, id=1)
        """
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session) -> int:
        """
        전체 레코드 수 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            int: 전체 레코드 수

        Example:
            total_users = crud_user.count(db)
        """
        return db.query(func.count(self.model.id)).scalar()

    def exists(self, db: Session, *, id: int) -> bool:
        """
        레코드 존재 여부 확인

        Args:
            db: 데이터베이스 세션
            id: 확인할 레코드의 ID

        Returns:
            bool: 존재 여부

        Example:
            if crud_user.exists(db, id=1):
                print("User exists")
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
