import uuid
from typing import Optional, Any
from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status
)
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.virtual_asset import (
    VirtualAsset,
    VirtualAssetRevision,
)
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

virtual_asset_router = APIRouter(
    prefix="/virtual_assets/{virtual_asset_id}/revisions",
    tags=["VirtualAssetRevision"]
)
router = APIRouter(
    prefix="/virtual_asset_revisions/{id}",
    tags=["VirtualAssetRevision"]
)
attr_router = APIRouter(
    prefix="/virtual_asset_revisions/{id}/{attr}",
    tags=["VirtualAssetRevision"]
)

@virtual_asset_router.post("", response_model=VirtualAssetRevision)
def create(virtual_asset_id: uuid.UUID, payload: VirtualAssetRevision, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{id}/virtual_assets
    """
    user_id = "unknown"
    virtual_asset = kls_get_by_id(VirtualAsset, virtual_asset_id, dbsession)
    payload.virtual_asset_id = virtual_asset_id
    payload.project_id = virtual_asset.project_id
    return kls_create(VirtualAssetRevision, user_id, payload, dbsession)

@router.get("", response_model=VirtualAssetRevision)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(VirtualAssetRevision, id, dbsession)

@router.put("", response_model=VirtualAssetRevision)
def update(id: uuid.UUID, payload: VirtualAssetRevision, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(VirtualAssetRevision, user_id, id, payload, dbsession)

@virtual_asset_router.get("", response_model=VirtualAssetRevision)
def get_revision_by_number(virtual_asset_id: uuid.UUID, number: int, dbsession: DBSession = Depends(get_session)):
    """ GET from /virtual_assets/{id}/revisions
    """
    virtual_asset = kls_get_by_id(VirtualAsset, virtual_asset_id, dbsession)
    try:
        return virtual_asset.get_revision(dbsession, number)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@virtual_asset_router.get("", response_model= list[VirtualAssetRevision])
def get_revisions_by_tags(virtual_asset_id: uuid.UUID, tag: list[str], dbsession: DBSession = Depends(get_session)):
    """ GET /virtual_assets/{id}/revisions?tag=&tag=
    """
    virtual_asset = kls_get_by_id(VirtualAsset, virtual_asset_id, dbsession)
    return virtual_asset.get_by_tags(dbsession, tag)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(VirtualAssetRevision, id, attr, dbsession)
