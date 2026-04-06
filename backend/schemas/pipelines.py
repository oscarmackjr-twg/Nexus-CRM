from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pipeline_id: UUID
    name: str
    position: int
    probability: Decimal
    stage_type: str
    rotting_days: int | None = None
    created_at: datetime


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    team_id: UUID | None = None
    name: str
    is_default: bool
    currency: str
    probability_model: str
    created_by: UUID
    is_archived: bool
    created_at: datetime
    stages: list[StageResponse] = []
