import uuid
from typing import Optional
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    status
)
from sqlmodel import (
    Session,
)
from ..models import get_session
from ..models.physical_asset import PhysicalAsset, EPhysicalAssetType
from ..models.project import Project

router = APIRouter()

@router.get("", response_model=list[PhysicalAsset])
def get_all_physical_asset(
    type: Optional[EPhysicalAssetType] = None,
    project_id: Optional[uuid.UUID] = None,
    dbsession: Session = Depends(get_session)
):
    project = None
    if project_id is not None:
        project = Project.get_by_id(project_id, dbsession)
        if project is None:
            return []
    return PhysicalAsset.get_all(
        dbsession,
        type_=type,
        project=project
    )

@router.post("", response_model=PhysicalAsset)
def create_physical_asset(physical_asset: PhysicalAsset, dbsession: Session = Depends(get_session)):
    return PhysicalAsset.create(physical_asset, dbsession)

@router.get("/{id}", response_model=PhysicalAsset)
def get_physical_asset_by_id(id: uuid.UUID, dbsession: Session = Depends(get_session)):
    physical_asset = PhysicalAsset.get_by_id(id, dbsession)
    if not physical_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"physical_asset id {id} Not Found"
        )
    return physical_asset

@router.put("/{id}", response_model=PhysicalAsset)
def update_physical_asset(id: uuid.UUID, physical_asset_data: PhysicalAsset, dbsession: Session = Depends(get_session)):
    physical_asset = PhysicalAsset.update(id, physical_asset_data, dbsession)
    if physical_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"physical_asset id {id} Not Found"
        )
    return physical_asset

@router.get("/", response_model=PhysicalAsset)
def get_by_code(code: str, dbsession: Session = Depends(get_session)):
    physical_asset = PhysicalAsset.get_by_code(dbsession, code)
    if physical_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"physical_asset code {code} Not Found"
        )
    return physical_asset

@router.get("/{id}/{attr}", response_model=PhysicalAsset)
def get_attrs(dbsession: Session = Depends(get_session)):
    pass
