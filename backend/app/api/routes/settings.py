"""Settings/Preferences API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.settings import (
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
)
from app.services import settings_service

router = APIRouter()


@router.get(
    "",
    response_model=UserPreferencesResponse,
    summary="Get current user preferences",
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferencesResponse:
    """Retrieve the current user's preferences.

    If preferences haven't been set yet, returns default values.
    """
    preferences = await settings_service.get_preferences(db, current_user.id)
    return UserPreferencesResponse.model_validate(preferences)


@router.put(
    "",
    response_model=UserPreferencesResponse,
    summary="Update user preferences",
    status_code=status.HTTP_200_OK,
)
async def update_settings(
    request: UserPreferencesUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferencesResponse:
    """Update the current user's preferences.

    Only fields provided in the request body will be updated.
    All fields are optional - omit fields you don't want to change.
    """
    preferences = await settings_service.update_preferences(
        db, current_user.id, request
    )
    return UserPreferencesResponse.model_validate(preferences)
