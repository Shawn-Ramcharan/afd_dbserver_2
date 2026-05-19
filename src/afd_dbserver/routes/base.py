from typing import Optional, Any
import uuid
from fastapi import HTTPException, status
from sqlmodel import Session as DBSession
from ..exc import BadRequestError, NotFoundError
from ..models.mixin import BaseMixin

def kls_get_owner_by_id[M: BaseMixin](
    id_: uuid.UUID,
    owner_kls_list: list[M],
    dbsession: DBSession
) -> M:
    owner_kls_names = ""
    for owner_kls in owner_kls_list:
        try:
            model = owner_kls.get_by_id(id_, dbsession)
            return model
        except NotFoundError:
            owner_kls_names += f"{owner_kls_names.__name__}, "
    owner_kls_names = owner_kls_names[:-2]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Could not find {id_=} for {owner_kls_names}"
    )

def kls_create[M: BaseMixin](
    klass_: M,
    user_id: str,
    payload: M,
    dbsession: DBSession
) -> M:
    try:
        return klass_.create(user_id, payload, dbsession)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

def kls_get_by_id[M: BaseMixin](
    klass_: M,
    id: uuid.UUID,
    dbsession: DBSession
) -> M:
    try:
        return klass_.get_by_id(id, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
def kls_update[M: BaseMixin](
    klass_: M,
    user_id: str,
    id: uuid.UUID,
    payload: M,
    dbsession: DBSession
) -> M:
    try:
        return klass_.update(user_id, id, payload, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

def kls_get_by_code[M: BaseMixin](
    klass_: M,
    code: str,
    dbsession: DBSession,
    parent_id: Optional[uuid.UUID] = None
) -> M:
    try:
        if parent_id:
            klass_.get_by_code(dbsession, parent_id, code)
        return klass_.get_by_code(dbsession, code)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

def kls_get_by_name[M: BaseMixin](
    klass_: M,
    name: str,
    dbsession: DBSession
) -> M:
    try:
        return klass_.get_by_name(dbsession, name)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

def kls_get_attrs[M: BaseMixin](
    klass_: M,
    id: uuid.UUID,
    attr: str,
    dbsession: DBSession,
    limit_: Optional[int] = None,
    offset_: Optional[int] = None
) -> Any:
    try:
        db_object = klass_.get_by_id(id, dbsession)
        return db_object.get_attr_relationship(attr, limit_=limit_, offset_=offset_)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
