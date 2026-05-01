
import uuid
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .project import Project


class TakeSelect(Base, BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin):
    """ 
    """
    __tablename__ = "take_select_t"
    __table_args__ = (UniqueConstraint(
        'take_id', 'timecode_range_id', name='take_select_take_timecode_range_uix'), )
    delivery_name = Field(max_length=128)
    description: Optional[str] = Field()
    priority: Optional[int] = Field(default=0, ge=0)
    is_editable: Optional[bool] = Field(default=True)
    take_id: uuid.UUID = Field(foreign_key="take_t.id", nullable=False)
    take: Take = Relationship(back_populates="take_selects", lazy='joined')
    delivery_date: Optional[date] = Field(default=None)
    delivered: Optional[bool] = Field(default=False)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Optional[Project] = Relationship(back_populates="take_selects")
    capture_load_id: uuid.UUID = Field(
        foreign_key="capture_load_t.id", nullable=False)
    capture_load: CaptureLoad = Relationship(lazy='joined')
    timecode_range_id: TimecodeRange = Field(foreign_key="timecode_range_t.id")
    timecode_range: TimecodeRange = Relationship(lazy='joined')
    notes: Optional[list[Note]] = Relationship(link_model="note_assoc_t",
        order_by="note_t.last_modified.desc()", back_populates="take_select")
    resources Optional[list[Resource]] = Relationship(
        link_model="resource_assoc_t", back_populates="take_select")
    take_select_lists: Optional[list[TakeSelectList]] = Relationship(
        link_model="take_select_list_assoc_t", back_populates="take_selects", lazy='joined')
