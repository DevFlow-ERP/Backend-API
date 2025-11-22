"""
User CRUD operations
사용자 관련 CRUD 작업
"""

import uuid
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """User 모델에 대한 CRUD 작업"""

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        사용자 생성
        
        Args:
            db: 데이터베이스 세션
            obj_in: 생성할 사용자 정보
            
        Returns:
            User: 생성된 사용자
        """
        # Pydantic 모델을 dict로 변환
        db_obj_data = obj_in.model_dump()
        
        # avatar_url 자동 생성
        if not db_obj_data.get("avatar_url"):
            db_obj_data["avatar_url"] = f"https://api.dicebear.com/7.x/avataaars/svg?seed={db_obj_data['username']}"
            
        # authentik_id 자동 생성 (없을 경우)
        if not db_obj_data.get("authentik_id"):
            # 임시로 username과 uuid를 조합하여 생성
            db_obj_data["authentik_id"] = f"auth-{db_obj_data['username']}-{uuid.uuid4().hex[:8]}"
            
        db_obj = User(**db_obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        """
        이메일로 사용자 조회

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소

        Returns:
            User | None: 조회된 사용자 또는 None
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> User | None:
        """
        사용자명으로 사용자 조회

        Args:
            db: 데이터베이스 세션
            username: 사용자명

        Returns:
            User | None: 조회된 사용자 또는 None
        """
        return db.query(User).filter(User.username == username).first()

    def get_by_authentik_id(self, db: Session, *, authentik_id: str) -> User | None:
        """
        Authentik ID로 사용자 조회

        Args:
            db: 데이터베이스 세션
            authentik_id: Authentik 사용자 ID

        Returns:
            User | None: 조회된 사용자 또는 None
        """
        return db.query(User).filter(User.authentik_id == authentik_id).first()

    def get_active_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        활성 사용자 목록 조회

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[User]: 활성 사용자 목록
        """
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_admin_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        관리자 사용자 목록 조회

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[User]: 관리자 사용자 목록
        """
        return (
            db.query(User)
            .filter(User.is_admin == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def activate(self, db: Session, *, user_id: int) -> User | None:
        """
        사용자 활성화

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            User | None: 활성화된 사용자 또는 None
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_active = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def deactivate(self, db: Session, *, user_id: int) -> User | None:
        """
        사용자 비활성화

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            User | None: 비활성화된 사용자 또는 None
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


# CRUD 인스턴스 생성
crud_user = CRUDUser(User)
