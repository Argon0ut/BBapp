from src.models.auth import AuthUser, UserRole
from src.repositories.auth_repository import AuthRepository
from src.schemas.clients import UserUpdateSchema


class UserService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    async def get_all_users(self) -> list[AuthUser]:
        return await self.auth_repo.get_all_users()

    async def get_user(self, user_id: int) -> AuthUser:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    async def update_user(
        self,
        target_user_id: int,
        payload: UserUpdateSchema,
        actor: AuthUser,
    ) -> AuthUser:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_user(target_user_id)

        if actor.role != UserRole.ADMIN.value:
            allowed_fields = {"full_name"}
            updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates and actor.role != UserRole.ADMIN.value:
            raise ValueError("Only admin can update role or status")

        if "role" in updates and updates["role"] is not None:
            updates["role"] = updates["role"].value

        updated = await self.auth_repo.update_user(target_user_id, updates)
        if not updated:
            raise ValueError("User not found")
        return updated

    async def delete_user(self, target_user_id: int, actor: AuthUser) -> dict:
        if actor.role != UserRole.ADMIN.value and actor.id != target_user_id:
            raise ValueError("You can only delete your own account")

        deleted = await self.auth_repo.delete_user(target_user_id)
        if not deleted:
            raise ValueError("User not found")
        return {"success": True}
