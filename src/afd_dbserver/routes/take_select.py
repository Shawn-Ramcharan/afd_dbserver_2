import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.take_select import TakeSelect
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

take_router = APIRouter(
    prefix="/takes/{volume_id}/take_selects",
    tags=["TakeSelects"]
)
router = APIRouter(
    prefix="/take_selects/{id}",
    tags=["TakeSelects"]
)
attr_router = APIRouter(
    prefix="/take_selects/{id}/{attrs}",
    tags=["TakeSelects"]
)

@take_router.post("", response_model=TakeSelect)
def create(take_id: uuid.UUID, payload: TakeSelect, dbsession: DBSession = Depends(get_session)):
    """ POST to /takes/{id}/take_selects
    Creates copies of the supplied CaptureLoad and TimecodeRange
    """
    user_id = "unknown"
    payload.take_id= take_id
    return kls_create(TakeSelect, user_id, payload, dbsession)

@router.get("", response_model=TakeSelect)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(TakeSelect, id, dbsession)

@router.put("", response_model=TakeSelect)
def update(id: uuid.UUID, payload: TakeSelect, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(TakeSelect, user_id, id, payload, dbsession)

@take_router.get("/", response_model=TakeSelect)
def get_by_code(volume_id: uuid.UUID, code: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /takes/{id}/take_selects?code=[code]
    """
    return kls_get_by_code(TakeSelect, code, dbsession, volume_id)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(TakeSelect, id, attr, dbsession)
