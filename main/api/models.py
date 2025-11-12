from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConvertResponse(BaseModel):
    data: Dict[str, Any]


class BatchConvertEntry(BaseModel):
    filename: str
    records: int
    data: Dict[str, Any]


class BatchConvertResponse(BaseModel):
    results: List[BatchConvertEntry]
    errors: List[Dict[str, str]]


class LetterPayload(BaseModel):
    filename: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class AliasAddRequest(BaseModel):
    canonical: str
    alias: str


class IgnoreColumnRequest(BaseModel):
    label: str
