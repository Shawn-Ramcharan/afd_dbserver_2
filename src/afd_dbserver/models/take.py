import uuid
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum as SqlaEnum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import ARRAY, Text
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Field, Column, select, not_)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from .note import Note, NoteAssoc
from ..exc import NotFoundError, BadRequestError

if TYPE_CHECKING:
    from .take_select import TakeSelect
    from .timecode_range import TimecodeRange
    from .session import Session
    from .capture_load import CaptureLoad


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
    delivery_name: Optional[str] = Field(default=None, max_length=128)
    slate: str = Field(max_length=128, nullable=False)
    number: int = Field(nullable=False, default=1, ge=1)
    type_: ETakeType = Field(
        sa_column=Column(SqlaEnum(ETakeType, name="etaketype"), nullable=False)
    )
    status: ETakeStatus = Field(
        sa_column=Column(SqlaEnum(ETakeStatus, name="etakestatus"), nullable=False)
    )
    tags: Optional[list[str]] = Field(default=None, sa_column=Column('tags', ARRAY(Text())))
    folder: Optional[str] = Field()
    session_id: Optional[uuid.UUID] = Field(default=None, foreign_key="session_t.id")
    session: "Session" = Relationship(back_populates="takes")
    capture_loads: list["CaptureLoad"] = Relationship(
        back_populates="take",
        sa_relationship_kwargs={
            # "order_by": "CaptureLoad.creation_date.desc()"
        }
    )
    timecode_ranges: list["TimecodeRange"] = Relationship(
        back_populates="take",
        sa_relationship_kwargs={
            "lazy": "joined",
            # "order_by": "TimecodeRange.creation_date.desc()",
        }
    )
    notes: list["Note"] = Relationship(
        back_populates="take",
        link_model=NoteAssoc,
        sa_relationship_kwargs={
            # "order_by": "Note.last_modified.desc()"
        }
    )
    take_selects: list["TakeSelect"] = Relationship(
        back_populates="take",
        sa_relationship_kwargs={
            # "order_by": "TakeSelect.creation_date.desc()"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="take"
    )

    @classmethod
    def get_all(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        type_: Optional[ETakeType] = None,
        omit_status: Optional[list[ETakeStatus]] = None
    ):
        stmt = select(cls).where(cls.project_id==project_id)
        if omit_status:
            if omit_status not in ETakeStatus.__members__:
                raise BadRequestError(f"Invalid status(s) {omit_status=}")
            stmt = stmt.where(not_(cls.status.in_(omit_status)))
        if type_:
            if type_ not in ETakeType.__members__:
                raise BadRequestError(f"Invalid type_ {type_=}")
            stmt = stmt.where(cls.type==type_)
        stmt.order_by(cls.creation_date.desc())
        return dbsession.exec(stmt).all()

    @classmethod
    def get_by_name(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        name: str
    ):
        try:
            return request.dbsession.query(cls).filter(and_(cls.project_id==project_id, cls.name==name)).one()
        except NoResultFound:
            raise HTTPNotFound("No Take found with project_id={0} and name={1}".format(project_id, name))

    @classmethod
    def get_by_slates(cls, request, project_id, slates):
        return request.dbsession.query(cls).filter(and_(cls.project_id==project_id,cls.slate.in_(slates))).order_by(desc(cls.name)).all()

    @classmethod
    def get_all_slates(cls, request, project_id):
        take_types = request.params.getall("types")
        query = request.dbsession.query(distinct(cls.slate)).filter(cls.project_id==project_id)
        if take_types is not None:
            query = query.filter(cls.type_.in_(take_types))
        return [s[0] for s in query.all()]

    @classmethod
    def get_next_take_from_slate(cls, request, project_id, slate):
        query = request.dbsession.query(cls.number).filter(and_(cls.project_id==project_id, cls.slate==slate))
        results = query.all()
        if len(results) == 0:
            return 1
        highest_value = sorted([v[0] for v in query.all()])[-1]
        return highest_value+1


