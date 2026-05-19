import uuid
from typing import Optional, Any
from fastapi import (
    Depends,
    APIRouter,
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.take import (
    Take,
    ETakeType,
    ETakeStatus
)
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_name,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/projects/{project_id}/takes",
    tags=["Takes"]
)
router = APIRouter(
    prefix="/takes/{id}", tags=["Takes"]
)
attr_router = APIRouter(
    prefix="/takes/{id}/{attr}", tags=["Takes"]
)

@project_router.get("", response_model=list[Take])
def get_all(
    project_id: uuid.UUID,
    type: Optional[ETakeType] = None,
    omit_status: Optional[list[ETakeStatus]] = None,
    dbsession: DBSession = Depends(get_session)
):
    """ GET from /project/{id}/takes?omit_status=queued&type=performance
    """
    return Take.get_all(
        dbsession,
        project_id,
        type,
        omit_status
    )

@project_router.post("", response_model=Take)
def create(project_id: uuid.UUID, payload: Take, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{id}/takes
    """
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(Take, user_id, payload, dbsession)

@router.get("", response_model=Take)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Take, id, dbsession)

@router.put("", response_model=Take)
def update(id: uuid.UUID, payload: Take, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Take, user_id, id, payload, dbsession)

@router.get("/", response_model=Take)
def get_by_name(name: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /project/{id}/takes?name=[take_name]
    """
    return kls_get_by_name(Take, name, dbsession)

@project_router.get("", response_model=list[Take])
def get_by_slate(project_id: uuid.UUID, slate: list[str], dbsession: DBSession = Depends(get_session)):
    """ GET from /project/{id}/takes?slate=[slate_name]&slate=...
    """
    return Take.get_by_slates(dbsession, project_id, slate)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Take, id, attr, dbsession)
