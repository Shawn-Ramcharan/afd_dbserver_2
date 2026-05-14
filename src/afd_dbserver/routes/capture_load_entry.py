import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models import CaptureLoadEntry
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

volume_router = APIRouter(
    prefix="/volumes/{volume_id}/device",
    tags=["CaptureLoadEntrys"]
)
router = APIRouter(
    prefix="/device/{id}",
    tags=["CaptureLoadEntrys"]
)
attr_router = APIRouter(
    prefix="/device/{id}/{attrs}",
    tags=["CaptureLoadEntrys"]
)

@volume_router.post("", response_model=CaptureLoadEntry)
def create(volume_id: uuid.UUID, payload: CaptureLoadEntry, dbsession: DBSession = Depends(get_session)):
    """ POST to /volumes/{volume_id}/device
    """
    user_id = "unknown"
    payload.volume_id = volume_id
    return kls_create(CaptureLoadEntry, user_id, payload, dbsession)

@router.get("", response_model=CaptureLoadEntry)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(CaptureLoadEntry, id, dbsession)

@router.put("", response_model=CaptureLoadEntry)
def update(id: uuid.UUID, payload: CaptureLoadEntry, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(CaptureLoadEntry, user_id, id, payload, dbsession)

@volume_router.get("/", response_model=CaptureLoadEntry)
def get_by_code(volume_id: uuid.UUID, code: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /volumes/{id}/device?code=[code]
    """
    return kls_get_by_code(CaptureLoadEntry, code, dbsession, volume_id)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(CaptureLoadEntry, id, attr, dbsession)
