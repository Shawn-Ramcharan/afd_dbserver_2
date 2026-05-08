from typing import Any, Optional
import uuid
from datetime import datetime, timezone
from sqlmodel import (Session, SQLModel, Field, JSON, select, delete)


def utcnow():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)


class IdMixin(SQLModel):
    """ID"""

    id: Optional[uuid.UUID] = Field(
        # sa_type=UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default_factory=uuid.uuid4,
    )

    @classmethod
    def get_by_id(cls, id: uuid.UUID, dbsession: Session):
        # return dbsessionn.get(cls, id)
        return dbsession.exec(select(cls).where(cls.id == id)).one()

class BaseMixin(IdMixin):
    """BaseMixin"""

    created_by: str = Field(nullable=False)
    creation_date: Optional[datetime] = Field(
        # sa_type=DateTime(timezone=True),
        default_factory=utcnow,
        nullable=False,
        # sa_column_kwargs={
        #     "server_default": utcnow
        # }
    )
    modified_by: str = Field(nullable=False)
    last_modified: Optional[datetime] = Field(
        # sa_type=DateTime(timezone=True),
        default_factory=utcnow,
        nullable=False,
        # sa_column_kwargs={
        #     # "server_default": utcnow,
        #     "onupdate": utcnow
        # },
    )

    @classmethod
    def create(cls, payload: SQLModel, dbsession: Session):
        model = cls.model_validate(payload)
        model.set_creation_stamp(dbsession)
        dbsession.add(model)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    @classmethod
    def update(cls, id_: uuid.UUID, payload: SQLModel, dbsession: Session):
        model = cls.get_by_id(id_, dbsession)
        model_data = cls.model_validate(payload)
        if not model:
            return None
        for field, value in model_data.model_dump().items():
            setattr(model, field, value)
        model.update_stamp(dbsession)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    def set_creation_stamp(self, dbsession: Session):
        # track the creating user
        # self.created_by = request.authenticated_userid
        # self.modified_by = request.authenticated_userid
        self.created_by = "shawn"
        self.modified_by = "shawn"

    def update_stamp(self, dbsession: Session):
        # track the modifying user
        # self.modified_by = request.authenticated_userid
        self.modified_by = "shawn"

class AttrMixin(SQLModel):
    """Extra Attributes to add in database."""

    attrs: Optional[dict] = Field(default=None, sa_type=JSON)

    def merge_attrs(self, attrs: dict[str, Any]):
        if self.attrs is None:
            self.attrs = {}
        for key, value in attrs.items():
            if value is None and key in self.attrs:
                self.attrs.pop(key)
            else:
                self.attrs.update({key: value})

class ProjectScopedDataMixin(object):

    @classmethod
    def get_all_by_project(cls, dbsession: Session, project_id: str):
        dbsession.expire_all()
        stmt = select(cls).where(cls.project_id == project_id)
        data_ = dbsession.scalars(stmt).unique().all()
        return data_

    @classmethod
    def get_all_ids_by_project(cls, dbsession: Session, project_id: str):
        dbsession.expire_all()
        stmt = select(cls.id).where(cls.project_id == project_id)
        data_ = dbsession.scalars(stmt).unique().all()
        return data_

    @classmethod
    def delete_all_by_project(cls, dbsession: Session, project_id: str):
        rows_affected = dbsession.exec(
            delete(cls).where(cls.project_id == project_id)
        ).rowcount
        dbsession.expire_all()
        return rows_affected


class ProjectScopedAssocMixin(object):

    PROJECT_ASSOC_CLS = None
    PROJECT_CLS_ATTR = None

    @classmethod
    def get_all_assoc_by_project(cls, dbsession: Session, project_id: str):
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
    def delete_all_assoc_by_project(cls, dbsession: Session, project_id: str):
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
    def get_all_by_project(cls, dbsession: Session, project_id: str):
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
    def delete_all_by_project(cls, dbsession: Session, project_id: str):
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
