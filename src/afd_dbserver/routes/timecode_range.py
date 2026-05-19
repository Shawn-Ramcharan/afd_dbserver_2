import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.timecode_range import TimecodeRange
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

router = APIRouter(
    prefix="/timecode_range/{id}",
    tags=["TimecodeRanges"]
)
attr_router = APIRouter(
    prefix="/timecode_range/{id}/{attrs}",
    tags=["TimecodeRanges"]
)

@router.post("", response_model=TimecodeRange)
def create(volume_id: uuid.UUID, payload: TimecodeRange, dbsession: DBSession = Depends(get_session)):
    """ POST to /volumes/{volume_id}/timecode_range
    """
    user_id = "unknown"
    payload.volume_id = volume_id
    return kls_create(TimecodeRange, user_id, payload, dbsession)

@router.get("", response_model=TimecodeRange)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(TimecodeRange, id, dbsession)

@router.put("", response_model=TimecodeRange)
def update(id: uuid.UUID, payload: TimecodeRange, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(TimecodeRange, user_id, id, payload, dbsession)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(TimecodeRange, id, attr, dbsession)
