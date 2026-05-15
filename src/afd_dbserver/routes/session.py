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

from afd_dbserver.models.take import ETakeType
from ..models import get_session
from ..models.session import Session
from ..exc import BadRequestError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/projects/{project_id}/sessions",
    tags=["Sessions"]
)
router = APIRouter(
    prefix="/sessions/{id}",
    tags=["Sessions"]
)
attr_router = APIRouter(
    prefix="/sessions/{id}/{attr}",
    tags=["Sessions"]
)

@project_router.post("", response_model=Session)
def create(project_id: uuid.UUID, payload: Session, dbsession: DBSession = Depends(get_session)):
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(Session, user_id, payload, dbsession)

@project_router.get("", response_model=list[Session | date])
def get_data(
    project_id: uuid.UUID,
    query: Optional[str] = None,
    name: Optional[str] = None,
    location_id: Optional[uuid.UUID] = None,
    dbsession: DBSession = Depends(get_session)
):
    """
    GET from /projects/{project_id}/sessions?&query=dates[&location_id=]
    GET from /projects/{project_id}/sessions?name=&[location_id=]
    """
    if name and query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Request cant query dates and name"
        )
    if query == "dates":
        return Session.get_all_dates(
            dbsession,
            project_id,
            location_id
        )
    if name:
        return Session.get_by_name(dbsession, project_id, name, location_id)

# NOTE: Just put `/all` for now but would
# like to change this to the original path
# designe.
@project_router.get("/all", response_model=list[Session])
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

@router.get("", response_model=Session)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Session, id, dbsession)

@router.put("", response_model=Session)
def update(id: uuid.UUID, session_data: Session, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Session, user_id, id, session_data, dbsession)

@attr_router.get("", response_model=Any)
def get_attrs(
    id: uuid.UUID,
    attr: str,
    type: Optional[ETakeType] = None,
    dbsession: DBSession = Depends(get_session)
):
    if attr != "take" and type is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot get types for {attr}"
        )
    if attr == "takes":
        session = kls_get_by_id(Session, id, dbsession)
        try:
            return session.get_takes(dbsession, type)
        except BadRequestError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )
    return kls_get_attrs(Session, id, attr, dbsession)
