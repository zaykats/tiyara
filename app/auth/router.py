from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import RefreshRequest, SignInRequest, SignUpRequest, TokenResponse
from app.auth.service import refresh_tokens, sign_in, sign_up
from app.dependencies import get_db, get_redis

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    payload: SignUpRequest,
    db: AsyncSession = Depends(get_db),
):
    return await sign_up(db, payload)


@router.post("/signin", response_model=TokenResponse)
async def signin(
    payload: SignInRequest,
    db: AsyncSession = Depends(get_db),
):
    return await sign_in(db, payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    return await refresh_tokens(db, redis, payload.refresh_token)
