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
from ..models.capture_load import (
    CaptureLoadEntry,
    CaptureLoadEntryVersion,
    CaptureLoadEntryVersionAddOrUpdate
)
from ..exc import NotFoundError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

capture_load_router = APIRouter(
    prefix="/capture_loads/{capture_id}/entries",
    tags=["CaptureLoadEntrys"]
)
router = APIRouter(
    prefix="/capture_load_entry/{id}",
    tags=["CaptureLoadEntrys"]
)
attr_router = APIRouter(
    prefix="/capture_load_entry/{id}/{attrs}",
    tags=["CaptureLoadEntrys"]
)
versions_router = APIRouter(
    prefix="/capture_load_entry/{id}/versions",
    tags=["CaptureLoadEntryVersions"]
)

# NOTE: cple version (CaptureLoadVersionVersion)
# Route is in here since to create cple version
# is created/update/removing by the CaptureLoadEntry
# and original code did not have a seperate file
# for cple version. Cple version also did not have
# an attrs route in the original code.
capture_load_entry_version_router = APIRouter(
    prefix="/capture_load_entry_versions/{id}",
    tags=["CaptureLoadEntryVersions"]
)

@capture_load_router.post("", response_model=CaptureLoadEntry)
def create(captur_load_id: uuid.UUID, payload: CaptureLoadEntry, dbsession: DBSession = Depends(get_session)):
    """ POST to /volumes/{volume_id}/device
    """
    user_id = "unknown"
    payload.capture_load_id = captur_load_id
    return kls_create(CaptureLoadEntry, user_id, payload, dbsession)

@router.get("", response_model=CaptureLoadEntry)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(CaptureLoadEntry, id, dbsession)

@router.put("", response_model=CaptureLoadEntry)
def update(id: uuid.UUID, payload: CaptureLoadEntry, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(CaptureLoadEntry, user_id, id, payload, dbsession)

@versions_router.post("/versions", response_model=CaptureLoadEntryVersion)
def add_or_update_version(id: uuid.UUID, payload: CaptureLoadEntryVersionAddOrUpdate, dbsession: DBSession = Depends(get_session)):
    """ POST to /capture_load_entry/{id}/versions
    """
    user_id = "john"
    cple_ = kls_get_by_id(CaptureLoadEntry, id, dbsession)
    cple_.add_or_update_version(
        dbsession,
        user_id,
        payload.name,
        payload.version_id,
        payload.attrs
    )

@versions_router.get("", response_model=CaptureLoadEntryVersion)
def get_version_by_name(id: uuid.UUID, name: str, dbsession: DBSession = Depends(get_session)):
    """ GET from /capture_load_entries/{id}/versions?name={name}
    """
    cple_ = kls_get_by_id(CaptureLoadEntry, id, dbsession)
    return cple_.get_version_by_name(dbsession, name)

@capture_load_entry_version_router.put("", response_model=CaptureLoadEntryVersion)
def update_version(id: uuid.UUID, payload: CaptureLoadEntryVersion, dbsession: DBSession = Depends(get_session)):
    """ PUT to /capture_load_entry_versions/{id}
    """
    user_id = "john"
    return kls_update(
        CaptureLoadEntryVersion,
        user_id,
        id,
        payload,
        dbsession
    )

@versions_router.delete("", response_model=None)
def remove_version(id: uuid.UUID, version_id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    """ DELETE to /capture_load_entry/{id}/versions
    """
    cple_ = kls_get_by_id(CaptureLoadEntry, id, dbsession)
    try:
        cple_.remove_version(dbsession, version_id)
    except NotFoundError as err:
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@versions_router.delete("", response_model=None)
def remove_version_by_name(id: uuid.UUID, name: str, dbsession: DBSession = Depends(get_session)):
    """ DELETE to /capture_load_entry/{id}/versions?name=
    """
    cple_ = kls_get_by_id(CaptureLoadEntry, id, dbsession)
    try:
        cple_.remove_version_by_name(dbsession, name)
    except NotFoundError as err:
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(CaptureLoadEntry, id, attr, dbsession)
