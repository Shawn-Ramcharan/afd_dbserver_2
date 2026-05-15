import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.volume import Volume
from ..exc import BadRequestError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

session_router = APIRouter(
    prefix="/sessions/{session_id}/virtual_assets",
    tags=["Volumes"]
)
router = APIRouter(
    prefix="/volumes/{id}",
    tags=["Volumes"]
)
attr_router = APIRouter(
    prefix="/volumes/{id}/{attrs}",
    tags=["Volumes"]
)

@session_router.post("", response_model=Volume)
def create(session_id: uuid.UUID, payload: Volume, dbsession: DBSession = Depends(get_session)):
    """ POST to /sessions/{id}/virtual_assets
    """
    user_id = "unknown"
    payload.session_id = session_id
    return kls_create(Volume, user_id, payload, dbsession)

@router.get("", response_model=Volume)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Volume, id, dbsession)

@router.put("", response_model=Volume)
def update(id: uuid.UUID, payload: Volume, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Volume, user_id, id, payload, dbsession)

@session_router.get("/", response_model=Volume)
def get_by_code(session_id: uuid.UUID, code: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /sesisons/{session_id}/volumes?code=[code]
    """
    return kls_get_by_code(Volume, code, dbsession, session_id)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Volume, id, attr, dbsession)
