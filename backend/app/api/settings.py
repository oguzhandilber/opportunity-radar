"""Settings API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Setting, get_session

router = APIRouter()


class SettingValue(BaseModel):
    """Setting value model."""

    value: dict | list | str | int | float | bool


@router.get("")
async def list_settings(session: AsyncSession = Depends(get_session)):
    """List all settings."""
    result = await session.execute(select(Setting))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}


@router.get("/{key}")
async def get_setting(key: str, session: AsyncSession = Depends(get_session)):
    """Get a specific setting."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"key": key, "value": None}
    return {"key": key, "value": setting.value}


@router.put("/{key}")
async def set_setting(
    key: str,
    setting: SettingValue,
    session: AsyncSession = Depends(get_session),
):
    """Set a setting value."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = setting.value
    else:
        new_setting = Setting(key=key, value=setting.value)
        session.add(new_setting)

    await session.commit()
    return {"key": key, "value": setting.value}


@router.delete("/{key}")
async def delete_setting(key: str, session: AsyncSession = Depends(get_session)):
    """Delete a setting."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        await session.delete(setting)
        await session.commit()
    return {"message": f"Setting '{key}' deleted"}
