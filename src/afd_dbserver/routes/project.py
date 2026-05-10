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
from ..exc import BadRequestError, NotFoundError

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=list[Project])
def get_all_project(
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
def create_project(project: Project, dbsession: DBSession = Depends(get_session)):
    user_id = "unknown"
    try:
        return Project.create(user_id, project, dbsession)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.get("/{id}", response_model=Project)
def get_project_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    try:
        return Project.get_by_id(id, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@router.put("/{id}", response_model=Project)
def update_project(id: uuid.UUID, project_data: Project, dbsession: DBSession = Depends(get_session)):
    try:
        return Project.update("shawn", id, project_data, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@router.get("/", response_model=Project)
def get_by_code(code: str, dbsession: DBSession = Depends(get_session)):
    try:
        return Project.get_by_code(dbsession, code)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

# FIXME: original route should be
# /projects/{clients}. for now not
# to break the rest of the code
# added as /project_clients
@router.get("_clients", response_model=list[dict])
def get_all_clients(is_active: Optional[bool] = None, dbsession: DBSession = Depends(get_session)):
    return Project.get_all_clients(
        dbsession,
        is_active=is_active
    )

@router.get("/{id}/locations", response_model=list[Location])
def get_all_locations(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    try:
        return Session.get_all_locations(dbsession, id)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@router.get("/{id}/{attr}", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    try:
        project = Project.get_by_id(id, dbsession)
        return project.get_attr_relationship(attr)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
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
