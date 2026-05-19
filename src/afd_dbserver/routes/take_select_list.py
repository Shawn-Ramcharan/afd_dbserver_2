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
from ..models.take_select_list import TakeSelectList, ETakeSelectListType
from .base import (
    kls_get_by_id,
    kls_update,
    kls_get_attrs,
    kls_create
)

project_router = APIRouter(
    prefix="/project/{project_id}/take_select_lists",
    tags=["TakeSelectLists"]
)
router = APIRouter(
    prefix="/take_select_lists/{id}",
    tags=["TakeSelectLists"]
)
attr_router = APIRouter(
    prefix="/take_select_lists/{id}/{attrs}",
    tags=["TakeSelectLists"]
)


@project_router.get("", response_model=TakeSelectList)
def get_all(project_id: uuid.UUID, type: Optional[ETakeSelectListType] = None, dbsession: DBSession = Depends(get_session)):
    """ GET from /project/{id}/take_select_lists?type=
    """
    return TakeSelectList.get_all(dbsession, project_id, type_=type)

@router.post("", response_model=TakeSelectList)
def create(payload: TakeSelectList, dbsession: DBSession = Depends(get_session)):
    """ POST to /take_select_lists/
    """
    user_id = "unknown"
    return kls_create(TakeSelectList, user_id, payload, dbsession)

@router.get("", response_model=TakeSelectList)
def get_by_id(id: uuid.UUID, dbsession: DBSession = Depends(get_session)):
    return kls_get_by_id(TakeSelectList, id, dbsession)

@router.put("", response_model=TakeSelectList)
def update(id: uuid.UUID, payload: TakeSelectList, dbsession: DBSession = Depends(get_session)):
    user_id = "shawn"
    return kls_update(TakeSelectList, user_id, id, payload, dbsession)

@router.post("", response_model=TakeSelectList)
def tsl_actions(id: uuid.UUID, action: str, take_select_ids: list[uuid.UUID], dbsession: DBSession = Depends(get_session)):
    """
    POST from /take_select_lists/{id}?action=add_take_selects
    POST from /take_select_lists/{id}?action=remove_take_selects
        Expects a list of TakeSelect ids in the post body
    
    POST from /take_select_lists/{id}?action=place_order
    """
    tsl_ = kls_get_by_id(TakeSelectList, id, dbsession)
    match action:
        case "add_take_selects":
            tsl_.add_take_selects(dbsession, take_select_ids)
        case "remove_take_selects":
            tsl_.remove_take_selects(dbsession, take_select_ids)
        case "place_order":
            tsl_.place_order(dbsession)
        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"invalid action for TakeSelectList: {action=}"
            )
    return tsl_

@attr_router.get("", response_model=Any)
def get_attrs(id: uuid.UUID, attr: str, dbsession: DBSession = Depends(get_session)):
    return kls_get_attrs(TakeSelectList, id, attr, dbsession)
