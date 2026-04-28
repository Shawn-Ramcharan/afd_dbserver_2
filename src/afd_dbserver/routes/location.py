import uuid
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
from ..models.location import Location

router = APIRouter()

@router.get("/locations", response_model=list[Location])
def get_all_location(dbsession: Session = Depends(get_session)):
    return Location.get_all(dbsession)

@router.post("/locations", response_model=Location)
def create_location(location: Location, dbsession: Session = Depends(get_session)):
    return Location.create(location, dbsession)

@router.get("/locations/{id}", response_model=Location)
def get_location_by_id(id: uuid.UUID, dbsession: Session = Depends(get_session)):
    location = Location.get_by_id(id, dbsession)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"location id {id} Not Found"
        )
    return location

@router.put("/locations/{id}", response_model=Location)
def update_location(id: uuid.UUID, location_data: Location, dbsession: Session = Depends(get_session)):
    location = Location.update(id, location_data, dbsession)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"location id {id} Not Found"
        )
    return location

@router.get("/locations/", response_model=Location)
def get_by_code(code: str, dbsession: Session = Depends(get_session)):
    location = Location.get_by_code(dbsession, code)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"location code {code} Not Found"
        )
    return location

@router.get("/locations/{id}/{attr}", response_model=Location)
def get_attrs(dbsession: Session = Depends(get_session)):
    pass
