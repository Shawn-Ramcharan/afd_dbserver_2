import uuid
import enum
from sqlalchemy import Enum as SqlaEnum
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, Column, select)
from .mixin import IdMixin, BaseMixin, AttrMixin, ProjectScopedDataMixin, ProjectScopedAssocMixin
from .project import Project


class ETakeSelectListType(enum.Enum):
    order = "order"
    wishlist = "wishlist"
    generic = "generic"


class TakeSelectListAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "take_select_list_assoc_t"
    __table_args__ = (
        PrimaryKeyConstraint(
            "id",
            "take_select_list_id",
            "take_select_id",
            name="pk_take_select_list_assoc_t",
        ),
    )
    take_select_list_id = Field(foreign_key="take_select_list_t.id")
    take_select_list: TakeSelectList = Relationship()
    take_select_id = Field(foreign_key="take_select_t.id")
    take_select: TakeSelect = Relationship()

class TakeSelectList(
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    SQLModel,
    table=True,
):
    """The TakeSelectList holds a list of TakeSelects for use, primarily, with
    client ordering. There are three types of list - 'order' and 'wishlist' for
    client ordering, and 'generic' for use in select post processing.

    The object keesps track of VirtualAsset placeholder names in the arbitrary
    attrs.  This is also where list-specific actions, such as enabling or
    disabling entries in the TakeSelect's CaptureLoad are tracked.

    The attrs are also used to store info such as when the list was submitted
    (if it is an order) and when that submission was confirmed by Animatrik.

    It's worth noting that a single TakeSelect can appear in multiple lists as
    the client may not order all the CaptureLoadEntries in a TakeSelect at the
    same time.

    """

    __tablename__ = "take_select_list_t"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            "type_",
            name="take_select_list_project_id_name_type_uix",
        ),
    )
    name: str = Field(max_length=128)
    type_: ETakeSelectListType = Field(
        sa_column=Column(
            SqlaEnum(ETakeSelectListType, name="etakeselectlisttype"), nullable=False
        )
    )
    is_editable: Optional[bool] = Field(default=True)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Optional[Project] = Relationship(
        back_populates="take_select_lists")
    take_selects: TakeSelect = Relationship(
        link_model="take_select_list_assoc_t",
        back_populates="take_select_lists",
    )
    PROJECT_ASSOC_CLS = TakeSelectListAssoc
    PROJECT_CLS_ATTR = "take_select_list_id"
