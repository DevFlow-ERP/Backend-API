"""
Team CRUD operations
팀 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.team import Team, TeamMember, TeamRole
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamMemberCreate,
    TeamMemberUpdate,
)


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    """Team 모델에 대한 CRUD 작업"""

    def get_by_name(self, db: Session, *, name: str) -> Team | None:
        """
        팀 이름으로 조회

        Args:
            db: 데이터베이스 세션
            name: 팀 이름

        Returns:
            Team | None: 조회된 팀 또는 None
        """
        return db.query(Team).filter(Team.name == name).first()

    def get_user_teams(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Team]:
        """
        사용자가 속한 팀 목록 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Team]: 팀 목록
        """
        return (
            db.query(Team)
            .join(TeamMember)
            .filter(TeamMember.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_team_members(
        self,
        db: Session,
        *,
        team_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[TeamMember]:
        """
        팀 멤버 목록 조회

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[TeamMember]: 팀 멤버 목록
        """
        return (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_member(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int,
        role: TeamRole = TeamRole.MEMBER
    ) -> TeamMember:
        """
        팀에 멤버 추가

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID
            role: 팀 역할

        Returns:
            TeamMember: 생성된 팀 멤버
        """
        team_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        return team_member

    def remove_member(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int
    ) -> TeamMember | None:
        """
        팀에서 멤버 제거

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID

        Returns:
            TeamMember | None: 삭제된 팀 멤버 또는 None
        """
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        )
        if team_member:
            db.delete(team_member)
            db.commit()
        return team_member

    def update_member_role(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int,
        role: TeamRole
    ) -> TeamMember | None:
        """
        팀 멤버 역할 변경

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID
            role: 새로운 역할

        Returns:
            TeamMember | None: 업데이트된 팀 멤버 또는 None
        """
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        )
        if team_member:
            team_member.role = role
            db.add(team_member)
            db.commit()
            db.refresh(team_member)
        return team_member

    def is_member(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int
    ) -> bool:
        """
        사용자가 팀 멤버인지 확인

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID

        Returns:
            bool: 멤버 여부
        """
        return (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        ) is not None

    def has_role(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int,
        role: TeamRole
    ) -> bool:
        """
        사용자가 특정 역할을 가지고 있는지 확인

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID
            role: 확인할 역할

        Returns:
            bool: 역할 보유 여부
        """
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        )
        return team_member.role == role if team_member else False


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    """TeamMember 모델에 대한 CRUD 작업"""

    def get_by_team_and_user(
        self,
        db: Session,
        *,
        team_id: int,
        user_id: int
    ) -> TeamMember | None:
        """
        팀 ID와 사용자 ID로 팀 멤버 조회

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            user_id: 사용자 ID

        Returns:
            TeamMember | None: 조회된 팀 멤버 또는 None
        """
        return (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        )


# CRUD 인스턴스 생성
crud_team = CRUDTeam(Team)
crud_team_member = CRUDTeamMember(TeamMember)
