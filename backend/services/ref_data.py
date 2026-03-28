from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import RefData, User
from backend.schemas.ref_data import RefDataCreate, RefDataResponse, RefDataUpdate


class RefDataService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def list_by_category(self, category: str, *, include_inactive: bool = False) -> list[RefDataResponse]:
        stmt = (
            select(RefData)
            .where(
                or_(
                    RefData.org_id == self.current_user.org_id,
                    RefData.org_id.is_(None),
                )
            )
            .where(RefData.category == category)
            .order_by(RefData.position, RefData.label)
        )
        if not include_inactive:
            stmt = stmt.where(RefData.is_active.is_(True))
        rows = (await self.db.execute(stmt)).scalars().all()
        return [RefDataResponse.model_validate(row) for row in rows]

    async def create(self, payload: RefDataCreate) -> RefDataResponse:
        item = RefData(
            org_id=self.current_user.org_id,
            category=payload.category,
            value=payload.value,
            label=payload.label,
            position=payload.position,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return RefDataResponse.model_validate(item)

    async def update(self, item_id: UUID, payload: RefDataUpdate) -> RefDataResponse:
        item = await self.db.scalar(select(RefData).where(RefData.id == item_id))
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ref data item not found")
        # Only allow editing org's own items or system defaults (org_id=None)
        if item.org_id is not None and item.org_id != self.current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another org's ref data")
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await self.db.commit()
        await self.db.refresh(item)
        return RefDataResponse.model_validate(item)
