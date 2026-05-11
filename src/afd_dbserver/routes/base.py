import uuid
from typing import Any
from fastapi import HTTPException, status
from sqlmodel import SQLModel
from sqlmodel import Session as DBSession
from ..exc import BadRequestError, NotFoundError

def kls_create(klass_: Any, user_id: str, payload: SQLModel, dbsession: DBSession):
    try:
        return klass_.create(user_id, payload, dbsession)
    except BadRequestError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

def kls_get_by_id(klass_: Any, id: uuid.UUID, dbsession: DBSession):
    try:
        return klass_.get_by_id(id, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
def kls_update(klass_: Any, user_id: str, id: uuid.UUID, payload: SQLModel, dbsession: DBSession):
    try:
        return klass_.update(user_id, id, payload, dbsession)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

def kls_get_by_code(klass_: Any, code: str, dbsession: DBSession):
    try:
        return klass_.get_by_code(dbsession, code)
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )

def kls_get_attrs(klass_: Any, id: uuid.UUID, attr: str, dbsession: DBSession):
    try:
        db_object = klass_.get_by_id(id, dbsession)
        return db_object.get_attr_relationship(attr)
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
