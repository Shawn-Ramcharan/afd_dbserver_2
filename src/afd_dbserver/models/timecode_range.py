import uuid
import enum
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import Enum as SqlaEnum
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, Column, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedParentMixin

if TYPE_CHECKING:
    from .take import Take

class ETimecodeRangeType(enum.Enum):
    capture = "capture"
    select = "select"
    client_select = "client_select"
    added_to_order = "added_to_order"
    ordered = "ordered"
    mark = "mark"
    process = "process"
    qc = "qc"

class TimecodeRange(
    BaseMixin, AttrMixin, ProjectScopedParentMixin, SQLModel, table=True
):
    __tablename__ = "timecode_range_t"
    tc_in: str = Field(max_length=32, nullable=False, default="00:00:00:00")
    tc_out: Optional[str] = Field(max_length=32)
    tc_rate: str = Field(max_length=32, nullable=False, default="")
    type_: ETimecodeRangeType = Field(
        sa_column=Column(
            SqlaEnum(ETimecodeRangeType, name="etimecoderangetype"), nullable=False
        )
    )
    frame_count: Optional[int] = Field(default=0, ge=0)
    description: Optional[str] = Field()
    take_id: uuid.UUID = Field(foreign_key="take_t.id")
    take: "Take" = Relationship(back_populates="timecode_ranges")
    PROJECT_PARENT_CLS: ClassVar = "Take"
    PROJECT_CLS_ATTR: ClassVar = "take_id"
