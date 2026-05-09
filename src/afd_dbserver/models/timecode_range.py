import uuid
import enum
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy import Enum as SqlaEnum
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Column)
from afd_timecode import Timecode
from .mixin import BaseMixin, AttrMixin, ProjectScopedParentMixin
from ..exc import NotFoundError, BadRequestError

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
    tc_out: Optional[str] = Field(default=None, max_length=32)
    tc_rate: str = Field(max_length=32, nullable=False, default="TCRate_30")
    type_: ETimecodeRangeType = Field(
        sa_column=Column(
            SqlaEnum(ETimecodeRangeType, name="etimecoderangetype"), nullable=False
        )
    )
    frame_count: Optional[int] = Field(default=0, ge=0)
    description: Optional[str] = Field()
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id", default=None)
    take: "Take" = Relationship(back_populates="timecode_ranges")
    PROJECT_PARENT_CLS: ClassVar = "Take"
    PROJECT_CLS_ATTR: ClassVar = "take_id"

    @classmethod
    def create(cls, user_id: str, payload: SQLModel, dbsession: DBSession):
        if payload.take_id is not None:
            cls.check_capture_status(dbsession, payload.take_id)
        timecode_ = Timecode()
        timecode_.set_from_string(payload.tc_in, payload.tc_rate)
        payload.frame_count = timecode_.frames
        model = super(TimecodeRange, cls).create(user_id, payload, dbsession)
        return model

    @staticmethod
    def check_capture_status(dbsession: DBSession, take_id: uuid.UUID | None):
        if take_id is None:
            return None
        from .take import Take
        take = Take.get_by_id(take_id, dbsession)
        if not take:
            raise NotFoundError(Take, take_id=take_id)
        for tc_range in take.timecode_ranges:
            if tc_range.type_ == ETimecodeRangeType.capture:
                raise BadRequestError(
                    "There is already a TimecodeRange with 'capture' "
                    f"status associated with this Take: {tc_range}"
                )

    def copy_tc(
        self,
        dbsession: DBSession,
        user_id: str,
        take_id: Optional[uuid.UUID] = None
    ):
        tc_range_copy = TimecodeRange(
            tc_in=self.tc_in,
            tc_out=self.tc_out,
            tc_rate=self.tc_rate,
            type_=self.type_,
            description=self.description,
            attrs=self.attrs,
            take_id=take_id,
            created_by=user_id,
            modified_by=user_id
        )
        dbsession.add(tc_range_copy)
        dbsession.commit()
        return tc_range_copy

    @classmethod
    def update(cls, id: uuid.UUID, payload: SQLModel, dbsession: DBSession):
        tc_range = TimecodeRange.get_by_id(id, dbsession)
        tc_range.check_capture_status(dbsession, payload.take_id)
        tc_range.merge_attrs(payload.attrs)
        model = BaseMixin.update(id, tc_range, dbsession)
        return model
