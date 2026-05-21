from typing import Any, Optional, Self, ClassVar
import uuid
import enum
from datetime import datetime, date, timezone
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.base import Mapped
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

    def __repr__(self):
        return f"<{self.__class__.__name__} : {self.id}>"

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
            relationship_kls  = getattr(self.__class__, relationship, None).mapper.class_.__name__
            match (limit_, offset_):
                case (int(), int()):
                    return (
                        relationship_kls,
                        getattr(self, relationship, None).offset(offset_).limit(limit_).all()
                    )
                case (int(), None):
                    return (
                        relationship_kls,
                        getattr(self, relationship, None).limit(limit_).all()
                    )
                case (None, int()):
                    return (
                        relationship_kls,
                        getattr(self, relationship, None).offset(offset_).all()
                    )
                case _:
                    attr_relationship = getattr(self, relationship, None)
                    if isinstance(attr_relationship, Query):
                        return (
                            relationship_kls,
                            attr_relationship.all()
                        )
                    if attr_relationship is None:
                        raise BadRequestError(
                            f"{self.__class__.__name__} does not have relationship {relationship}"
                        )
                    return (relationship_kls, attr_relationship)
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

def all_subclasses(cls):
    return set(cls.__subclasses__()).union([
        s for c in cls.__subclasses__() for s in all_subclasses(c)
    ])

def all_enum_classes():

    class_enum_types = []
    for enum_ in all_subclasses(enum.Enum):
        if not enum_.__module__.startswith("afd_dbserver.models"):
            continue
        class_enum_types.append(enum_)
    return class_enum_types

def get_object_meta():
    TYPES_ = {
        str: "string",
        int: "int",
        float: "float",
        bool: "bool",
        uuid.UUID: "uuid",
        list: "list",
        dict: "dict",
        datetime: "datetime",
        date: "date",
        Optional[str]: "string",
        Optional[int]: "int",
        Optional[float]: "float",
        Optional[bool]: "bool",
        Optional[uuid.UUID]: "uuid",
        Optional[list]: "list",
        Optional[dict]: "dict",
        Optional[datetime]: "datetime",
        Optional[date]: "date",
        Optional[list[str]]: "list",
    }
    ENUMS_TYPES_ = {enum_: enum_ for enum_ in all_enum_classes()}
    results = {}
    for kls in all_subclasses(IdMixin):
        kls_name = kls.__name__
        # Ignore BaseMixin
        if kls_name == "BaseMixin":
            continue
        # we handle these as a special case.
        # This is handled at the end of.
        if kls_name in ["ItemAssoc", "Item"]:
            continue
        if kls_name not in results.keys():
            results.update({
                kls_name: {"attributes": {}, "relationships": {}
            }})
        # Iter through the class attrs to get name and type.
        for attr_name, attr_type_ in kls.__annotations__.items():
            if attr_type_ == ClassVar:
                continue
            attr_ = getattr(kls, attr_name, None)
            if attr_ is None:
                continue
            # Add Enums of the model. This get also the
            # valid types for the enum.
            try:
                enum_ = ENUMS_TYPES_[attr_type_]
                results[kls_name]["attributes"].update({
                    attr_name: {
                        "type": "enum",
                        "valid_values": [str(type_) for type_ in enum_.__members__]
                    }
                })
                continue
            except KeyError:
                pass
            # Add Attributes of the model and its type_
            try:
                type_ = TYPES_[attr_type_]
                manditory_ = (attr_.nullable == False)
                results[kls_name]["attributes"].update({attr_name: {
                    "type": type_,
                    "mandatory": manditory_
                }})
            except KeyError:
                # Add Relationship of the model. This gets
                # the class for the relationship
                if isinstance(attr_, Mapped):
                    results[kls_name]["relationships"].update({
                        attr_name: {"target_class": attr_.mapper.class_.__name__}
                    })
    # Add the Items Meta Data
    results.update({
        "Item": {
            "attributes": {
                "name": {"type": "string", "mandatory": False},
                "location": {"type": "string", "mandatory": False},
                "attrs": {"type": "dict", "mandatory": False},
                "id": {"type": "uuid", "mandatory": True},
                "created_by": {"type": "string", "mandatory": True},
                "creation_date": {"type": "datetime", "mandatory": True},
                "modified_by": {"type": "string", "mandatory": True},
                "last_modified": {"type": "datetime", "mandatory": True},
            },
            "relationships": {"version": {"target_class": "Version"}},
        }
    })
    results["Version"]["relationships"]["items"] = {"target_class": "Item"}
    return results
