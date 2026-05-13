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
from ..models import SolverSetup
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/projects/{project_id}/solver_setups",
    tags=["SolverSetups"]
)

router = APIRouter(
    prefix="/solver_setups/{id}",
    tags=["SolverSetups"]
)
attr_router = APIRouter(
    prefix="/solver_setups/{id}/{attrs}",
    tags=["SolverSetups"]
)

@project_router.get("", response_model=list[SolverSetup])
def get_all(project_id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    """ GET to /physical_assets/{id}/solver_setups?project_id=
    """
    return SolverSetup.get_all(dbsession, project_id)

@project_router.post("", response_model=SolverSetup)
def create(project_id: uuid.UUID, payload: SolverSetup, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{id}/solver_setups
    """
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(SolverSetup, user_id, payload, dbsession)

@router.get("", response_model=SolverSetup)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(SolverSetup, id, dbsession)

@router.put("", response_model=SolverSetup)
def update(id: uuid.UUID, payload: SolverSetup, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(SolverSetup, user_id, id, payload, dbsession)

@router.get("", response_model=SolverSetup)
def get(source_id: uuid.UUID, target_id: uuid.UUID, name: str, dbsession: DBSession = Depends(get_session)):
    """ GET to /physical_assets/{id}/solver_setups?virtual_asset_revision_id=&name=
    """
    try:
        return Mapping.get(dbsession, source_id, target_id, name)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(SolverSetup, id, attr, dbsession)
