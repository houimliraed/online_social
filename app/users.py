import uuid 
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import FastAPIUsers, models, BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase 
from app.db import User, get_user_db


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret =  SECRET
    verification_token_secret = SECRET
    
    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        return await super().on_after_register(user, request)
    
    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None) -> None:
        return await super().on_after_forgot_password(user, token, request)
    
async def get_user_manager(user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db)):
    yield UserManager(user_db)

BearerTransport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

AuthenticationBackend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport,
    get_strategy=get_jwt_strategy,
)

FastAPIUsers = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [AuthenticationBackend],
)   
current_active_user = FastAPIUsers.current_user(active=True)