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
from ..models.virtual_asset import VirtualAsset
from ..exc import BadRequestError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/projects/{project_id}/virtual_assets",
    tags=["VirtualAssets"]
)
router = APIRouter(
    prefix="/virtual_assets/{id}",
    tags=["VirtualAssets"]
)
attr_router = APIRouter(
    prefix="/virtual_assets/{id}/{attrs}",
    tags=["VirtualAssets"]
)

@project_router.post("", response_model=VirtualAsset)
def create(project_id: uuid.UUID, payload: VirtualAsset, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{id}/virtual_assets
    """
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(VirtualAsset, user_id, payload, dbsession)

@router.get("", response_model=VirtualAsset)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(VirtualAsset, id, dbsession)

@router.put("", response_model=VirtualAsset)
def update(id: uuid.UUID, payload: VirtualAsset, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(VirtualAsset, user_id, id, payload, dbsession)

@project_router.get("/", response_model=VirtualAsset)
def get_by_code(project_id: uuid.UUID, code: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /project/{id}/virtual_assets?code=[code]
    """
    return kls_get_by_code(VirtualAsset, code, dbsession, project_id)

@project_router.get("/", response_model=list[VirtualAsset])
def get_by_type(project_id: uuid.UUID, type: str , dbsession: DBSession = Depends(get_session)):
    try:
        return VirtualAsset.get_all_by_type(dbsession, project_id, type)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(VirtualAsset, id, attr, dbsession)
