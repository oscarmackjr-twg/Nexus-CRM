from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import Contact, User
from backend.schemas.contacts import ContactActivityCreate, ContactCreate, ContactListResponse, ContactResponse, ContactUpdate
from backend.schemas.deals import ActivityResponse, DealResponse
from backend.services.contacts import ContactService
from backend.workers.automation_trigger import fire_trigger

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    page: int = 1,
    size: int = 25,
    search: str | None = None,
    lifecycle_stage: str | None = None,
    company_id: UUID | None = None,
    owner_id: UUID | None = None,
    tags: list[str] | None = Query(default=None),
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContactListResponse:
    return await ContactService(db, current_user).list_contacts(
        page=page,
        size=size,
        search=search,
        lifecycle_stage=lifecycle_stage,
        company_id=company_id,
        owner_id=owner_id,
        tags=tags,
        include_archived=include_archived,
    )


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContactResponse:
    response = await ContactService(db, current_user).create_contact(payload)
    background_tasks.add_task(
        fire_trigger,
        "contact_created",
        {"contact": response.model_dump(mode="json")},
        str(current_user.org_id),
    )
    return response


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContactResponse:
    return await ContactService(db, current_user).get_contact(contact_id)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContactResponse:
    return await ContactService(db, current_user).update_contact(contact_id, payload)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await ContactService(db, current_user).delete_contact(contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{contact_id}/linkedin-sync", response_model=ContactResponse)
async def sync_contact_linkedin(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContactResponse:
    if not current_user.linkedin_access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LinkedIn account not connected")
    contact = await db.get(Contact, contact_id)
    if contact is not None and contact.org_id == current_user.org_id:
        contact.linkedin_synced_at = datetime.now(timezone.utc)
        await db.commit()
    return await ContactService(db, current_user).get_contact(contact_id)


@router.get("/{contact_id}/deals", response_model=list[DealResponse])
async def get_contact_deals(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DealResponse]:
    return await ContactService(db, current_user).get_contact_deals(contact_id)


@router.get("/{contact_id}/activities", response_model=list[ActivityResponse])
async def get_contact_activities(
    contact_id: UUID,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ActivityResponse]:
    return await ContactService(db, current_user).get_contact_activities(contact_id, limit=limit)


@router.post("/{contact_id}/activities", status_code=status.HTTP_201_CREATED)
async def log_contact_activity(
    contact_id: UUID,
    data: ContactActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    activity = await ContactService(db, current_user).log_contact_activity(
        contact_id=contact_id,
        activity_type=data.activity_type,
        notes=data.notes,
        occurred_at=data.occurred_at,
        deal_id=data.deal_id,
    )
    return {
        "id": str(activity.id),
        "activity_type": activity.activity_type,
        "body": activity.body,
        "occurred_at": activity.occurred_at.isoformat(),
        "contact_id": activity.contact_id,
        "deal_id": str(activity.deal_id) if activity.deal_id else None,
    }
