from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.auth import AuthSession, AuthUser


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        result = await self.session.execute(
            select(AuthUser).where(AuthUser.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> AuthUser | None:
        result = await self.session.execute(
            select(AuthUser).where(AuthUser.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, payload: dict) -> AuthUser:
        user = AuthUser(**payload)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_all_users(self) -> list[AuthUser]:
        result = await self.session.execute(select(AuthUser))
        return result.scalars().all()

    async def update_user(self, user_id: int, updates: dict) -> AuthUser | None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for field, value in updates.items():
            setattr(user, field, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def create_session(self, payload: dict) -> AuthSession:
        user_session = AuthSession(**payload)
        self.session.add(user_session)
        await self.session.commit()
        await self.session.refresh(user_session)
        return user_session

    async def get_session_by_token(self, session_token: str) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSession).where(AuthSession.session_token == session_token)
        )
        return result.scalar_one_or_none()

    async def delete_session_by_token(self, session_token: str) -> bool:
        result = await self.session.execute(
            delete(AuthSession).where(AuthSession.session_token == session_token)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_expired_sessions(self, now: datetime) -> None:
        await self.session.execute(delete(AuthSession).where(AuthSession.expires_at < now))
        await self.session.commit()
