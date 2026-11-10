from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import Pipeline, User
from backend.schemas.pipelines import PipelineResponse

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/", response_model=list[PipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[PipelineResponse]:
    """Return the caller's organization pipelines and ordered stages for deal creation."""
    result = await db.scalars(
        select(Pipeline)
        .where(Pipeline.org_id == current_user.org_id, Pipeline.is_archived.is_(False))
        .options(selectinload(Pipeline.stages))
        .order_by(Pipeline.is_default.desc(), Pipeline.name)
    )
    pipelines = result.unique().all()
    for pipeline in pipelines:
        pipeline.stages.sort(key=lambda stage: stage.position)
    return [PipelineResponse.model_validate(pipeline) for pipeline in pipelines]
