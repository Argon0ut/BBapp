from datetime import datetime, timedelta, timezone

from src.config import Settings
from src.models.auth import AuthUser
from src.repositories.auth_repository import AuthRepository
from src.schemas.auth import LoginSchema, RegisterUserSchema
from src.services.security import create_session_token, hash_password, verify_password


class AuthService:
    def __init__(self, repo: AuthRepository, settings: Settings):
        self.repo = repo
        self.settings = settings

    async def register(self, payload: RegisterUserSchema) -> AuthUser:
        email = payload.email.strip().lower()
        existing = await self.repo.get_user_by_email(email)
        if existing:
            raise ValueError("User with this email already exists")

        user = await self.repo.create_user(
            {
                "email": email,
                "password_hash": hash_password(payload.password),
                "full_name": payload.full_name,
                "role": payload.role.value,
                "is_active": True,
            }
        )
        return user

    async def authenticate(self, payload: LoginSchema) -> AuthUser:
        user = await self.repo.get_user_by_email(payload.email.strip().lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("User is inactive")
        return user

    async def login(self, payload: LoginSchema) -> tuple[AuthUser, str, datetime]:
        user = await self.authenticate(payload)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.settings.session_ttl_hours)

        await self.repo.delete_expired_sessions(now)

        session_token = create_session_token()
        await self.repo.create_session(
            {
                "user_id": user.id,
                "session_token": session_token,
                "expires_at": expires_at,
            }
        )
        return user, session_token, expires_at

    async def logout(self, session_token: str) -> bool:
        return await self.repo.delete_session_by_token(session_token)

    async def get_user_by_session_token(self, session_token: str) -> AuthUser | None:
        now = datetime.now(timezone.utc)
        session = await self.repo.get_session_by_token(session_token)
        if not session:
            return None

        if session.expires_at < now:
            await self.repo.delete_session_by_token(session_token)
            return None

        return await self.repo.get_user_by_id(session.user_id)
