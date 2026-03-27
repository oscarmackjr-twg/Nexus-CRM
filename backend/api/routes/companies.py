from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import Company, User
from backend.schemas.companies import CompanyCreate, CompanyListResponse, CompanyResponse, CompanyUpdate
from backend.schemas.contacts import ContactResponse
from backend.schemas.deals import DealResponse
from backend.services.companies import CompanyService
from backend.workers.automation_trigger import fire_trigger

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    page: int = 1,
    size: int = 25,
    search: str | None = None,
    industry: str | None = None,
    size_range: str | None = None,
    owner_id: UUID | None = None,
    tags: list[str] | None = Query(default=None),
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CompanyListResponse:
    return await CompanyService(db, current_user).list_companies(
        page=page,
        size=size,
        search=search,
        industry=industry,
        size_range=size_range,
        owner_id=owner_id,
        tags=tags,
        include_archived=include_archived,
    )


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    response = await CompanyService(db, current_user).create_company(payload)
    background_tasks.add_task(
        fire_trigger,
        "company_created",
        {"company": response.model_dump(mode="json")},
        str(current_user.org_id),
    )
    return response


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    return await CompanyService(db, current_user).get_company(company_id)


@router.put("/{company_id}", response_model=CompanyResponse)
@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    return await CompanyService(db, current_user).update_company(company_id, payload)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await CompanyService(db, current_user).delete_company(company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{company_id}/linkedin-sync", response_model=CompanyResponse)
async def sync_company_linkedin(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    if not current_user.linkedin_access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LinkedIn account not connected")
    company = await db.get(Company, company_id)
    if company is not None and company.org_id == current_user.org_id:
        company.linkedin_synced_at = datetime.now(timezone.utc)
        await db.commit()
    return await CompanyService(db, current_user).get_company(company_id)


@router.get("/{company_id}/contacts", response_model=list[ContactResponse])
async def get_company_contacts(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ContactResponse]:
    return await CompanyService(db, current_user).get_company_contacts(company_id)


@router.get("/{company_id}/deals", response_model=list[DealResponse])
async def get_company_deals(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DealResponse]:
    return await CompanyService(db, current_user).get_company_deals(company_id)
