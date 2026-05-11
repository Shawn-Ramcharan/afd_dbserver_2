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
from ..models.location import Location
from ..models.session import Session
from ..models.take import Take
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

router = APIRouter(prefix="/projects", tags=["projects"])
attr_router = APIRouter(prefix="/projects/{id}/{attrs}", tags=["projects"])

@router.get("", response_model=list[Project])
def get_all(
    is_active: Optional[bool] = None,
    client_code: Optional[str] = None,
    dbsession: DBSession = Depends(get_session)
):
    return Project.get_all(
        dbsession,
        client_code=client_code,
        is_active=is_active
    )

@router.post("", response_model=Project)
def create(project: Project, dbsession: DBSession = Depends(get_session)):
    user_id = "unknown"
    return kls_create(Project, user_id, project, dbsession)

@router.get("/clients", response_model=list[dict])
def get_all_clients(is_active: Optional[bool] = None, dbsession: DBSession = Depends(get_session)):
    return Project.get_all_clients(
        dbsession,
        is_active=is_active
    )

@router.get("/{id}", response_model=Project)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Project, id, dbsession)

@router.put("/{id}", response_model=Project)
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
