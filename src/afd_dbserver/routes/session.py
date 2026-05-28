import uuid
from typing import Optional, Any
from datetime import date
from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    Request,
    status
)
from sqlmodel import Session as DBSession

from afd_dbserver.models.take import ETakeType, Take
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
def get_sessions(
    project_id: uuid.UUID,
    request: Request,
    query: Optional[str] = None,
    name: Optional[str] = None,
    location_id: Optional[uuid.UUID] = None,
    location_ids: Optional[list[uuid.UUID]] = None,
    shoot_dates: Optional[list[date]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    dbsession: DBSession = Depends(get_session)
):
    """
    GET from /projects/{project_id}/sessions?&query=dates[&location_id=]
    GET from /projects/{project_id}/sessions?name=&[location_id=]
    GET from /projects/{project_id}/sessions?[location_id=][&location_id=...][&shoot_date=][&shoot_date=...][&query=dates]
    """
    if name and query and (location_ids or shoot_dates or limit or offset):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This is an Invalid Request {request.url}"
        )
    if query == "dates":
        return Session.get_all_dates(
            dbsession,
            project_id,
            location_id
        )
    if name:
        return Session.get_by_name(
            dbsession,
            project_id,
            name,
            location_id
        )
    return Session.get_all(
        dbsession,
        project_id,
        location_ids=location_ids,
        shoot_dates=shoot_dates,
        limit_=limit,
        offset_=offset
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
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    type: Optional[ETakeType] = None,
    dbsession: DBSession = Depends(get_session)
):
    if attr != "take" and type is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot get types for {attr}"
        )
    if attr == "takes":
        try:
            takes_ = Take.get_all(
                dbsession,
                session_id=id,
                type_=type,
                limit_=limit,
                offset_=offset
            )
            return {
                "__class__": Take.__name__,
                "data": takes_
            }
        except BadRequestError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )
    return kls_get_attrs(Session, id, attr, dbsession, limit_=limit, offset_=offset)
