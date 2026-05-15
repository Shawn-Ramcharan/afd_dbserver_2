import uuid
from typing import Optional, Any
from fastapi import Depends, APIRouter
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.physical_asset import PhysicalAsset, EPhysicalAssetType
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

router = APIRouter(prefix="/physical_assets", tags=["PhysicalAssets"])
attr_router = APIRouter(prefix="/physical_assets/{id}/{attr}", tags=["PhysicalAssets"])

@router.get("", response_model=list[PhysicalAsset])
def get_all(
    type: Optional[EPhysicalAssetType] = None,
    project_id: Optional[uuid.UUID] = None,
    dbsession: DBSession = Depends(get_session)
):
    return PhysicalAsset.get_all(
        dbsession,
        type_=type,
        project_id=project_id
    )

@router.post("", response_model=PhysicalAsset)
def create(physical_asset: PhysicalAsset, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_create(PhysicalAsset, user_id, physical_asset, dbsession)

@router.get("/{id}", response_model=PhysicalAsset)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(PhysicalAsset, id, dbsession)

@router.put("/{id}", response_model=PhysicalAsset)
def update(id: uuid.UUID, physical_asset_data: PhysicalAsset, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(PhysicalAsset, user_id, id, physical_asset_data, dbsession)

@router.get("/", response_model=PhysicalAsset)
def get_by_code(code: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_code(PhysicalAsset, code, dbsession)

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(PhysicalAsset, id, attr, dbsession)
