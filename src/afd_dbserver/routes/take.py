import uuid
from typing import Optional, Any
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    status
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.project import Project
from ..models.take import Take, ETakeType, ETakeStatus
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(prefix="/projects/{project_id}/takes", tags=["takes"])
router = APIRouter(prefix="/takes/{id}", tags=["takes"])
attr_router = APIRouter(prefix="/takes/{id}/{attrs}", tags=["takes"])

@project_router.get("", response_model=list[Project])
def get_all(
    project_id: uuid.UUID,
    type: Optional[ETakeType] = None,
    omit_status: Optional[list[ETakeStatus]] = None,
    dbsession: DBSession = Depends(get_session)
):
    return Take.get_all(
        dbsession,
        project_id,
        type,
        omit_status
    )

@project_router.post("", response_model=Take)
def create(project_id: uuid.UUID, payload: Take, dbsession: DBSession = Depends(get_session)):
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(Take, user_id, payload, dbsession)

@router.get("", response_model=Project)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Project, id, dbsession)

@router.put("", response_model=Project)
def update(id: uuid.UUID, project_data: Project, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Project, user_id, id, project_data, dbsession)

@router.get("/", response_model=Project)
def get_by_code(code: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_code(Project, code, dbsession)

@router.get("/{id}/locations", response_model=list[Location])
def get_all_locations(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    try:
        return Session.get_all_locations(dbsession, id)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@router.get("/{id}/slate", response_model=int)
def get_next_take_from_slate(id: uuid.UUID, slate: str, dbsession: DBSession = Depends(get_session)):
    try:
        return Take.get_next_take_from_slate(
            dbsession,
            id,
            slate
        )
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    if attr == "slates":
        return Take.get_all_slates(dbsession, id)
    return kls_get_attrs(Project, id, attr, dbsession)
