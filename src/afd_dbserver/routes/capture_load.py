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
from ..models.capture_load import CaptureLoad
from ..models.take import Take
from ..models.volume import Volume
from ..exc import BadRequestError
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/project/{project_id}/capture_loads",
    tags=["CaptureLoads"]
)
router = APIRouter(
    prefix="/capture_loads/{id}",
    tags=["CaptureLoads"]
)
attr_router = APIRouter(
    prefix="/capture_loads/{id}/{attrs}",
    tags=["CaptureLoads"]
)

def _get_cpl_owner(payload: CaptureLoad, dbsession: DBSession):
    if payload.volume_id is not None:
        return kls_get_by_id(Volume, payload.volume_id, dbsession)
    elif payload.take_id is not None:
        return kls_get_by_id(Take, payload.take_id, dbsession)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need to supply a Take or Volume id to copy to"
        )

@project_router.post("", response_model=CaptureLoad)
def create(project_id: uuid.UUID, payload: CaptureLoad, dbsession: DBSession = Depends(get_session)):
    """ POST to /project/{project_id}/capture_loads
    """
    user_id = "unknown"
    payload.project_id = project_id
    return kls_create(CaptureLoad, user_id, payload, dbsession)

@router.get("", response_model=CaptureLoad)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(CaptureLoad, id, dbsession)

@router.put("", response_model=CaptureLoad)
def update(id: uuid.UUID, payload: CaptureLoad, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(CaptureLoad, user_id, id, payload, dbsession)

@router.post("", response_model=CaptureLoad)
def copy_to(
    id: uuid.UUID,
    action: str,
    payload: CaptureLoad,
    enabled_entries_only: Optional[bool] = True,
    dbsession = Depends(get_session)
):
    """ POST to /capture_loads/{id}?action=copy_to&enabled_entries_only=

    Copies this CaptureLoad to the target volume or take specified in the 
    params.  If 'enabled_entries_only' is specified in the params, only
    enabled CaptureLoadEntries are copied.
    """
    user_id = "jennifer"
    if action == "copy_to":
        cpl_ = kls_get_by_id(CaptureLoad, id, dbsession)
        target_owner = _get_cpl_owner(payload, dbsession)
        try:
            return cpl_.copy_cpl(
                dbsession,
                user_id,
                target_owner,
                enabled_entries_only=enabled_entries_only
            )
        except BadRequestError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )
@project_router.get("", response_model=list[CaptureLoad])
def get_by_tag(
    project_id: uuid.UUID,
    volume_id: Optional[uuid.UUID],
    take_id: Optional[uuid.UUID],
    tags: list[str],
    dbsession: DBSession = Depends(get_session)
):
    """ GET /projects/{id}/capture_loads?[volume_id=][take_id=]&tag=&tag=
    """
    return CaptureLoad.get_capture_loads_by_tags(
        dbsession,
        tags=tags,
        take_id=take_id,
        volume_id=volume_id,
    )

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(CaptureLoad, id, attr, dbsession)
