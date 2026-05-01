from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlmodel import (Session, SQLModel, Field, JSON, select, delete)


def utcnow():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)


class IdMixin(SQLModel):
    """ID"""

    id: uuid.UUID = Field(
        # sa_type=UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default_factory=uuid.uuid4,
    )

    @classmethod
    def get_by_id(cls, id: uuid.UUID, dbsession: Session):
        return dbsession.exec(select(cls).where(cls.id == id)).one()


class BaseMixin(IdMixin):
    """BaseMixin"""

    created_by: str = Field(nullable=False)
    creation_date: datetime = Field(
        # sa_type=DateTime(timezone=True),
        default_factory=utcnow,
        nullable=False,
        # sa_column_kwargs={
        #     "server_default": utcnow
        # }
    )
    modified_by: str = Field(nullable=False)
    last_modified: datetime = Field(
        # sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={
            # "server_default": utcnow,
            "onupdate": utcnow
        },
    )

    @classmethod
    def create(cls, payload: SQLModel, dbsession: Session):
        model = cls.model_validate(payload)
        model.set_creation_stamp(None)
        dbsession.add(model)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    @classmethod
    def update(cls, id: uuid.UUID, payload: SQLModel, dbsession: Session):
        model = cls.get_by_id(id, dbsession)
        model_data = cls.model_validate(payload)
        if not model:
            return None
        for field, value in model_data.model_dump().items():
            setattr(model, field, value)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    def set_creation_stamp(self, request):
        pass
        # track the creating user
        # self.created_by = request.authenticated_userid
        # self.modified_by = request.authenticated_userid

    def update_stamp(self, request):
        pass
        # track the modifying user
        # self.modified_by = request.authenticated_userid


class AttrMixin(SQLModel):
    """Extra Attributes to add in database."""

    attrs: Optional[dict] = Field(default=None, sa_type=JSON)


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
        rows_affected = dbsession.execute(
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
        rows_affected = dbsession.execute(
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
        rows_affected = dbsession.execute(
            delete(cls).where(cls_parent_cls_id_column.in_(parent_data_ids))
        ).rowcount
        dbsession.expire_all()
        return rows_affected
