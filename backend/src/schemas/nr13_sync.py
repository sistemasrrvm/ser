"""Schemas para sincronização NR13 via API Botset (#292)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SyncEntityResult(BaseModel):
    success: bool
    total: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    message: Optional[str] = None


class Nr13SyncResponse(BaseModel):
    success: bool
    data_ref: str
    results: SyncEntityResult
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Nr13NightlySyncResponse(BaseModel):
    success: bool
    data_ref: str
    results: dict[str, SyncEntityResult]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = None
