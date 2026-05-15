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
from ..models.mapping import Mapping
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/projects/{project_id}/mappings",
    tags=["Mappings"]
)
router = APIRouter(
    prefix="/mappings/{id}",
    tags=["Mappings"]
)
attr_router = APIRouter(
    prefix="/mappings/{id}/{attrs}",
    tags=["Mappings"]
)

@project_router.get("", response_model=list[Mapping])
def get_all(project_id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return Mapping.get_all(dbsession, project_id)

@project_router.post("", response_model=Mapping)
def create(project_id: uuid.UUID, payload: Mapping, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{id}/virtual_assets
    """
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(Mapping, user_id, payload, dbsession)

@router.get("", response_model=Mapping)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Mapping, id, dbsession)

@router.put("", response_model=Mapping)
def update(id: uuid.UUID, payload: Mapping, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Mapping, user_id, id, payload, dbsession)

@router.get("", response_model=Mapping)
def get(source_id: uuid.UUID, target_id: uuid.UUID, name: str, dbsession: DBSession = Depends(get_session)):
    try:
        return Mapping.get(dbsession, source_id, target_id, name)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Mapping, id, attr, dbsession)
