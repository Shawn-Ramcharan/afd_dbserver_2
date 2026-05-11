import uuid
from typing import Optional, Any
from fastapi import Depends, APIRouter
from sqlmodel import Session as DBSession
from ..models import get_session
from ..models.appliance import Appliance, EApplianceType
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_by_code,
    kls_get_attrs,
    kls_create
)

router = APIRouter(prefix="/appliances", tags=["appliances"])

@router.get("", response_model=list[Appliance])
def get_all(
    inactive: Optional[bool] = None,
    type: Optional[EApplianceType] = None,
    dbsession: DBSession = Depends(get_session)
):
    if inactive is None:
        inactive = False
    return Appliance.get_all(
        dbsession,
        type_=type,
        include_inactive=inactive
    )

@router.post("", response_model=Appliance)
def create(appliance: Appliance, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_create(Appliance, user_id, appliance, dbsession)

@router.get("/{id}", response_model=Appliance)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(Appliance, id, dbsession)

@router.put("/{id}", response_model=Appliance)
def update(id: uuid.UUID, appliance_data: Appliance, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(Appliance, user_id, id, appliance_data, dbsession)

@router.get("/", response_model=Appliance)
def get_by_code(code: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_code(Appliance, code, dbsession)

@router.get("/{id}/{attr}", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(Appliance, id, attr, dbsession)
