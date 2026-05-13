import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import Note
from ..models import get_session
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)
from . import (
    take,
    session
)

router = APIRouter(prefix="/notes/{id}", tags=["Notes"])
attr_router = APIRouter(prefix="/notes/{id}/{attr}", tags=["Notes"])

@take.attr_router.post("", response_model=Note, tags=["Notes"])
def create_take_note(id: uuid.UUID, attr: str, payload: Note, dbsession: DBSession = Depends(get_session)):
    user_id = "brian"
    if attr == "notes":
        payload.take_id = id
        payload.session_id = None
        payload.take_select_id = None
    return kls_create(Note, user_id, payload, dbsession)

@session.attr_router.post("", response_model=Note, tags=["Notes"])
def create_session_note(id: uuid.UUID, attr: str, payload: Note, dbsession: DBSession = Depends(get_session)):
    user_id = "brian"
    if attr == "notes":
        payload.take_id = None
        payload.session_id = id
        payload.take_select_id = None
    return kls_create(Note, user_id, payload, dbsession)

@router.get("", response_model=Note)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Note, id, dbsession)

@router.put("", response_model=Note)
def update(id: uuid.UUID, payload: Note, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Note, user_id, id, payload, dbsession)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Note, id, attr, dbsession)
