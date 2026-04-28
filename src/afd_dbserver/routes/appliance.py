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
from ..models.appliance import Appliance, EApplianceType

router = APIRouter()

@router.get("/appliances", response_model=list[Appliance])
def get_all_appliance(
    inactive: Optional[bool] = None,
    type: Optional[EApplianceType] = None,
    dbsession: Session = Depends(get_session)
):
    if inactive is None:
        inactive = False
    return Appliance.get_all(
        dbsession,
        type_=type,
        include_inactive=inactive
    )

@router.post("/appliances", response_model=Appliance)
def create_appliance(appliance: Appliance, dbsession: Session = Depends(get_session)):
    return Appliance.create(appliance, dbsession)

@router.get("/appliances/{id}", response_model=Appliance)
def get_appliance_by_id(id: uuid.UUID, dbsession: Session = Depends(get_session)):
    appliance = Appliance.get_by_id(id, dbsession)
    if not appliance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"appliance id {id} Not Found"
        )
    return appliance

@router.put("/appliances/{id}", response_model=Appliance)
def update_appliance(id: uuid.UUID, appliance_data: Appliance, dbsession: Session = Depends(get_session)):
    appliance = Appliance.update(id, appliance_data, dbsession)
    if appliance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"appliance id {id} Not Found"
        )
    return appliance

@router.get("/appliances/", response_model=Appliance)
def get_by_code(code: str, dbsession: Session = Depends(get_session)):
    appliance = Appliance.get_by_code(dbsession, code)
    if appliance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"appliance code {code} Not Found"
        )
    return appliance

@router.get("/appliances/{id}/{attr}", response_model=Appliance)
def get_attrs(dbsession: Session = Depends(get_session)):
    pass
