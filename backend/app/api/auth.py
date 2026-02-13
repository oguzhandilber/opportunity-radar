"""Authentication API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session, User, Workspace
from app.auth.jwt_handler import JWTHandler
from app.auth.password_manager import password_manager

router = APIRouter()
jwt_handler = JWTHandler()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str | None = None
    description: str | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user."""
    payload = jwt_handler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user and create default workspace."""

    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Validate password
    is_valid, errors = password_manager.validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(errors)}",
        )

    # Create user
    user = User(
        email=user_data.email,
        password_hash=password_manager.hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_verified=False,
        email_verification_token=password_manager.generate_verification_token(),
    )

    session.add(user)
    await session.flush()  # Get user.id

    # Create default workspace
    slug = user_data.email.split("@")[0].lower().replace(".", "-")
    workspace = Workspace(
        name=f"{user_data.first_name}'s Workspace",
        slug=slug,
        description="Your personal workspace",
        created_by=user.id,
    )

    session.add(workspace)
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Authenticate user and return tokens."""

    # Find user by email
    stmt = select(User).where(User.email == form_data.username, User.is_active == True)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not password_manager.verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    user_data = {"user_id": user.id, "email": user.email, "role": "owner"}

    tokens = jwt_handler.generate_tokens(user_data)

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await session.commit()

    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    tokens = jwt_handler.refresh_access_token(refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)
