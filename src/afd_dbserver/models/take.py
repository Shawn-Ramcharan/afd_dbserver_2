import uuid
import enum
from typing import Optional
from sqlalchemy import Enum as SqlaEnum
from sqlmodel import (SQLModel, Field, Relationship, Field, Column)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .project import Project


class ETakeType(enum.Enum):
    test = "test"
    scale = "scale"
    ROM = "ROM"
    performance = "performance"
    camera = "camera"
    calibration = "calibration"


class ETakeStatus(enum.Enum):
    ng = "ng"
    good = "good"
    buy = "buy"
    star = "star"
    queued = "queued"


class Take(
    BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True
):
    """ """

    __tablename__ = "take_t"
    __table_args__ = (
        UniqueConstraint("name", "project_id", name="take_name_project_uix"),
    )
    name: str = Field(max_length=128, nullable=False)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="takes")
    delivery_name: Optional[str] = Field(max_length=128)
    slate: str = Field(max_length=128, nullable=False)
    number: int = Field(nullable=False, default=1, ge=1)
    type_: ETakeType = Field(
        sa_column=Column(SqlaEnum(ETakeType, name="etaketype"), nullable=False)
    )
    status: ETakeStatus = Field(
        sa_column=Column(SqlaEnum(ETakeStatus, name="etakestatus"), nullable=False)
    )
    tags: Optional[list[str]] = Field(default=[])
    folder: Optional[str] = Field()
    session_id: Optional[uuid.UUID] = Field(foreign_key="session_t.id")
    session: Optional["Session"] = Relationship(back_populates="takes")
    capture_loads: Optional[list["CaptureLoad"]] = Relationship(
        back_populates="take", order_by="CaptureLoad.creation_date.desc()"
    )
    timecode_ranges: Optional[list["TimecodeRange"]] = Relationship(
        back_populates="take",
        lazy="joined",
        order_by="TimecodeRange.creation_date.desc()",
    )
    notes: Optional[list["Note"]] = Relationship(
        "Note", secondary="note_assoc_t", order_by="Note.last_modified.desc()"
    )
    take_selects: Optional[list["TakeSelect"]] = Relationship(
        back_populates="take", order_by="TakeSelect.creation_date.desc()"
    )
    resources: Optional[list["Resource"]] = Relationship(
        link_model="resource_assoc_t", back_populates="takes"
    )
