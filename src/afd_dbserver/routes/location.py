import uuid
from typing import Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.location import Location
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("", response_model=list[Location])
def get_all(dbsession: DBSession = Depends(get_session)):
    return Location.get_all(dbsession)

@router.post("", response_model=Location)
def create(location: Location, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_create(Location, user_id, location, dbsession)

@router.get("/{id}", response_model=Location)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Location, id, dbsession)

@router.put("/{id}", response_model=Location)
def update(id: uuid.UUID, location_data: Location, dbsession: DBSession = Depends(get_session)):
    user_id ="shawn"
    return kls_update(Location, user_id, id, location_data, dbsession)

@router.get("/", response_model=Location)
def get_by_code(code: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_code(Location, code, dbsession)

@router.get("/{id}/{attr}", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Location, id, attr, dbsession)
