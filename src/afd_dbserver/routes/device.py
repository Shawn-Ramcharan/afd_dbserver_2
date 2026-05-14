import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models import Device
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

volume_router = APIRouter(
    prefix="/volumes/{volume_id}/device",
    tags=["Devices"]
)
router = APIRouter(
    prefix="/device/{id}",
    tags=["Devices"]
)
attr_router = APIRouter(
    prefix="/device/{id}/{attrs}",
    tags=["Devices"]
)

@volume_router.post("", response_model=Device)
def create(volume_id: uuid.UUID, payload: Device, dbsession: DBSession = Depends(get_session)):
    """ POST to /volumes/{volume_id}/device
    """
    user_id = "unknown"
    payload.volume_id = volume_id
    return kls_create(Device, user_id, payload, dbsession)

@router.get("", response_model=Device)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Device, id, dbsession)

@router.put("", response_model=Device)
def update(id: uuid.UUID, payload: Device, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Device, user_id, id, payload, dbsession)

@volume_router.get("/", response_model=Device)
def get_by_code(volume_id: uuid.UUID, code: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /volumes/{id}/device?code=[code]
    """
    return kls_get_by_code(Device, code, dbsession, volume_id)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Device, id, attr, dbsession)
