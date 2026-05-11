import uuid
from typing import Optional, Any
from datetime import date
from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.project import Project
from ..models.session import Session
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["sessions"])
router = APIRouter(prefix="/sessions", tags=["sessions"])
attr_router = APIRouter(prefix="/sessions/{id}/{attrs}", tags=["projects"])

@project_router.post("", response_model=Session)
def create(project: Project, dbsession: DBSession = Depends(get_session)):
    user_id = "unknown"
    return kls_create(Session, user_id, project, dbsession)

@project_router.get("_a", response_model=list[Session])
def get_all(
    project_id: uuid.UUID,
    location_ids: Optional[list[uuid.UUID]] = None,
    shoot_dates: Optional[list[date]] = None,
    dbsession: DBSession = Depends(get_session)
):

    """
    GET from /projects/{project_id}/sessions?[location_id=][&location_id=...][&shoot_date=][&shoot_date=...][&query=dates]
    """
    return Session.get_all(
        dbsession,
        project_id,
        location_ids=location_ids,
        shoot_dates=shoot_dates
    )

@project_router.get("", response_model=list[date])
def get_all_dates(
    project_id: uuid.UUID,
    query: str,
    location_id: Optional[uuid.UUID] = None,
    dbsession: DBSession = Depends(get_session)
):
    """ GET from /projects/{id}/sessions?&query=dates[&location_id=]
    """
    if query == "dates":
        return Session.get_all_dates(
            dbsession,
            project_id,
            location_id
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid Query {query}"
    )

@router.get("/{id}", response_model=Session)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Session, id, dbsession)

@router.put("/{id}", response_model=Session)
def update(id: uuid.UUID, session_data: Session, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Session, user_id, id, session_data, dbsession)

@project_router.get("", response_model=list[Session])
def get_by_name(
    project_id: uuid.UUID,
    name: str,
    location_id: Optional[uuid.UUID] = None,
    dbsession: DBSession = Depends(get_session)
):
    """ GET from /projects/{id}/sessions?name=&[location_id=]
    """
    return Session.get_by_name(dbsession, project_id, name, location_id)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Session, id, attr, dbsession)
