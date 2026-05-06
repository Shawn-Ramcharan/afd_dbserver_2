
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .resource_mixin import ResourceMixin
from .project import Project
from .note import Note, NoteAssoc
from .resource import Resource, ResourceAssoc
from .take_select_list import TakeSelectList, TakeSelectListAssoc

if TYPE_CHECKING:
    from .timecode_range import TimecodeRange
    from .capture_load import CaptureLoad
    from .take import Take

class TakeSelect(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ 
    """

    CLS_ID_ATTR: ClassVar = "take_select_id"
    __tablename__ = "take_select_t"
    __table_args__ = (UniqueConstraint(
        'take_id', 'timecode_range_id', name='take_select_take_timecode_range_uix'), 
    )
    delivery_name: Optional[str] = Field(max_length=128, default=None)
    description: Optional[str] = Field(default=None)
    priority: Optional[int] = Field(default=0, ge=0)
    is_editable: Optional[bool] = Field(default=True)
    take_id: uuid.UUID = Field(foreign_key="take_t.id", nullable=False)
    take: "Take" = Relationship(
        back_populates="take_selects",
        sa_relationship_kwargs={"lazy": "joined"}
    )
    # delivery_date: Optional[date] = Field(default=None)
    # delivered: Optional[bool] = Field(default=False)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="take_selects")
    capture_load_id: uuid.UUID = Field(
        foreign_key="capture_load_t.id", nullable=False)
    capture_load: "CaptureLoad" = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    timecode_range_id: uuid.UUID = Field(foreign_key="timecode_range_t.id")
    timecode_range: "TimecodeRange" = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    notes: list["Note"] = Relationship(
        link_model=NoteAssoc,
        back_populates="take_select",
        sa_relationship_kwargs={
            "order_by": "note_t.last_modified.desc()",
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="take_select"
    )
    take_select_lists: list["TakeSelectList"] = Relationship(
        link_model=TakeSelectListAssoc,
        back_populates="take_selects",
        sa_relationship_kwargs={
            "lazy": "joined"
        }
    )
