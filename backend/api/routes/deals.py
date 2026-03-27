from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import User
from backend.schemas.deals import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    DealCreate,
    DealListResponse,
    DealMoveStage,
    DealResponse,
    DealUpdate,
)
from backend.services.deals import DealService
from backend.utils.telemetry import deal_created_counter, deal_won_counter
from backend.workers.automation_trigger import fire_trigger

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/", response_model=DealListResponse)
async def list_deals(
    pipeline_id: UUID | None = None,
    stage_id: UUID | None = None,
    owner_id: UUID | None = None,
    team_id: UUID | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    tags: list[str] | None = Query(default=None),
    page: int = 1,
    size: int = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealListResponse:
    return await DealService(db, current_user).list_deals(
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        owner_id=owner_id,
        team_id=team_id,
        status=status_value,
        search=search,
        tags=tags,
        page=page,
        size=size,
    )


@router.post("/", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    response = await DealService(db, current_user).create_deal(payload)
    deal_created_counter.inc(org_id=str(current_user.org_id))
    background_tasks.add_task(fire_trigger, "deal_created", {"deal": response.model_dump(mode="json")}, str(current_user.org_id))
    return response


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await DealService(db, current_user).get_deal(deal_id)


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    payload: DealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await DealService(db, current_user).update_deal(deal_id, payload)


@router.patch("/{deal_id}", response_model=DealResponse)
async def patch_deal(
    deal_id: UUID,
    payload: DealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await DealService(db, current_user).update_deal(deal_id, payload)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await DealService(db, current_user).delete_deal(deal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{deal_id}/move-stage", response_model=DealResponse)
async def move_deal_stage(
    deal_id: UUID,
    payload: DealMoveStage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    response = await DealService(db, current_user).move_stage(deal_id, payload)
    background_tasks.add_task(
        fire_trigger,
        "deal_stage_change",
        {"deal": response.model_dump(mode="json")},
        str(current_user.org_id),
    )
    if response.status == "won":
        deal_won_counter.inc(org_id=str(current_user.org_id))
        background_tasks.add_task(fire_trigger, "deal_won", {"deal": response.model_dump(mode="json")}, str(current_user.org_id))
    if response.status == "lost":
        background_tasks.add_task(fire_trigger, "deal_lost", {"deal": response.model_dump(mode="json")}, str(current_user.org_id))
    return response


@router.get("/{deal_id}/activities", response_model=ActivityListResponse)
async def get_deal_activities(
    deal_id: UUID,
    page: int = 1,
    size: int = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityListResponse:
    return await DealService(db, current_user).get_deal_activities(deal_id, page=page, size=size)


@router.post("/{deal_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def log_deal_activity(
    deal_id: UUID,
    payload: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityResponse:
    return await DealService(db, current_user).log_activity(deal_id, payload)
