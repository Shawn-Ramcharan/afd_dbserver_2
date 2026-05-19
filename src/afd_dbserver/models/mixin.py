from typing import Any, Optional, Self
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.query import Query
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, Field, JSON, select, delete, desc
from ..exc import NotFoundError, BadRequestError


def utcnow():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)


class IdMixin(SQLModel):
    """ID"""

    id: Optional[uuid.UUID] = Field(
        primary_key=True,
        unique=True,
        nullable=False,
        default_factory=uuid.uuid4,
    )

    @classmethod
    def get_by_id(cls, id_: uuid.UUID, dbsession: DBSession):
        try:
            return dbsession.exec(select(cls).where(cls.id == id_)).unique().one()
        except NoResultFound:
            raise NotFoundError(cls, id_=id_)


class BaseMixin(IdMixin):
    """BaseMixin"""

    created_by: str = Field(nullable=False)
    creation_date: Optional[datetime] = Field(
        default_factory=utcnow,
        nullable=False,
    )
    modified_by: str = Field(nullable=False)
    last_modified: Optional[datetime] = Field(
        default_factory=utcnow,
        nullable=False,
    )

    @classmethod
    def create(cls, user_id: str, payload: Self, dbsession: DBSession):
        payload.set_creation_stamp(user_id)
        model = cls.model_validate_json(payload.model_dump_json())
        try:
            dbsession.add(model)
        except IntegrityError as err:
            raise BadRequestError(err)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    @classmethod
    def update(cls, user_id: str, id_: uuid.UUID, payload: Self, dbsession: DBSession):
        model = cls.get_by_id(id_, dbsession)
        model.update_stamp(user_id)
        attrs = getattr(payload, "attrs", None)
        if issubclass(cls, AttrMixin) and attrs is not None:
            model.merge_attrs(attrs)
        for field, value in payload.model_dump().items():
            if field == "id":
                continue
            setattr(model, field, value)
        # model = cls.model_validate(model)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    def get_attr_relationship(
        self,
        relationship: str,
        limit_: Optional[int] = None,
        offset_: Optional[int] = None,
    ):
        try:
            match (limit_, offset_):
                case (int(), int()):
                    return getattr(self, relationship, None).offset(offset_).limit(limit_).all()
                case (int(), None):
                    return getattr(self, relationship, None).limit(limit_).all()
                case (None, int()):
                    return getattr(self, relationship, None).offset(offset_).all()
                case _:
                    attr_relationship = getattr(self, relationship, None)
                    if isinstance(attr_relationship, Query):
                        return attr_relationship.all()
                    if attr_relationship is None:
                        raise BadRequestError(
                            f"{self.__class__.__name__} does not have relationship {relationship}"
                        )
                    return attr_relationship
        except AttributeError as err:
            raise BadRequestError(
                f"Something went wrong when trying to access {relationship} for {self.__class__.__name__} limit={limit_}, offset={offset_}"
            )

    def set_creation_stamp(self, user_id: str):
        # track the creating user
        self.created_by = user_id
        self.creation_date = utcnow()
        self.modified_by = user_id
        self.last_modified = utcnow()

    def update_stamp(self, user_id: str):
        # track the modifying user
        self.modified_by = user_id
        self.last_modified = utcnow()


class AttrMixin(SQLModel):
    """Extra Attributes to add in database."""

    attrs: Optional[dict] = Field(sa_type=JSON)

    def merge_attrs(self, attrs: dict[str, Any]):
        if self.attrs is None:
            self.attrs = {"test": "test"}
        self.attrs.update(attrs)
        for key, value in self.attrs.items():
            if value is None:
                self.attrs.pop(key)


class ProjectScopedDataMixin(object):

    @classmethod
    def get_all_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        dbsession.expire_all()
        stmt = (
            select(cls)
            .where(cls.project_id == project_id)
            .order_by(desc(cls.creation_date))
        )
        data_ = dbsession.scalars(stmt).unique().all()
        return data_

    @classmethod
    def get_all_ids_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        dbsession.expire_all()
        stmt = select(cls.id).where(cls.project_id == project_id)
        data_ = dbsession.scalars(stmt).unique().all()
        return data_

    @classmethod
    def delete_all_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        rows_affected = dbsession.exec(
            delete(cls).where(cls.project_id == project_id)
        ).rowcount
        dbsession.expire_all()
        return rows_affected


class ProjectScopedAssocMixin(object):

    PROJECT_ASSOC_CLS = None
    PROJECT_CLS_ATTR = None

    @classmethod
    def get_all_assoc_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        dbsession.expire_all()
        project_data_ids = cls.get_all_ids_by_project(dbsession, project_id)
        if cls.PROJECT_CLS_ATTR is None:
            cls_attr_id = f"{cls.__name__.lower()}_id"
        else:
            cls_attr_id = cls.PROJECT_CLS_ATTR
        assoc_id_column = getattr(cls.PROJECT_ASSOC_CLS, cls_attr_id)
        stmt_2 = select(cls.PROJECT_ASSOC_CLS).where(
            assoc_id_column.in_(project_data_ids)
        )
        data_ = dbsession.scalars(stmt_2).all()
        return data_

    @classmethod
    def delete_all_assoc_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        dbsession.expire_all()
        project_data_ids = cls.get_all_ids_by_project(dbsession, project_id)
        if cls.PROJECT_CLS_ATTR is None:
            cls_attr_id = f"{cls.__name__.lower()}_id"
        else:
            cls_attr_id = cls.PROJECT_CLS_ATTR
        assoc_id_column = getattr(cls.PROJECT_ASSOC_CLS, cls_attr_id)
        rows_affected = dbsession.exec(
            delete(cls.PROJECT_ASSOC_CLS).where(assoc_id_column.in_(project_data_ids))
        ).rowcount
        dbsession.expire_all()
        return rows_affected


class ProjectScopedParentMixin(object):

    PROJECT_PARENT_CLS = None
    PROJECT_CLS_ATTR = None

    @classmethod
    def get_all_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        dbsession.expire_all()
        parent_data_ids = cls.PROJECT_PARENT_CLS.get_all_ids_by_project(
            dbsession, project_id
        )
        if cls.PROJECT_CLS_ATTR is None:
            cls_attr_id = f"{cls.PROJECT_PARENT_CLS.__name__.lower()}_id"
        else:
            cls_attr_id = cls.PROJECT_CLS_ATTR
        cls_parent_cls_id_column = getattr(cls, cls_attr_id)
        stmt = select(cls).where(cls_parent_cls_id_column.in_(parent_data_ids))
        data_ = dbsession.scalars(stmt).all()
        return data_

    @classmethod
    def delete_all_by_project(cls, dbsession: DBSession, project_id: uuid.UUID):
        parent_data_ids = cls.PROJECT_PARENT_CLS.get_all_ids_by_project(
            dbsession, project_id
        )
        if cls.PROJECT_CLS_ATTR is None:
            cls_attr_id = f"{cls.PROJECT_PARENT_CLS.__name__.lower()}_id"
        else:
            cls_attr_id = cls.PROJECT_CLS_ATTR
        cls_parent_cls_id_column = getattr(cls, cls_attr_id)
        rows_affected = dbsession.exec(
            delete(cls).where(cls_parent_cls_id_column.in_(parent_data_ids))
        ).rowcount
        dbsession.expire_all()
        return rows_affected
