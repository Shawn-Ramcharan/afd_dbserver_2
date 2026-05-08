import uuid
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum as SqlaEnum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import ARRAY, Text
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Field, Column)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from .note import Note, NoteAssoc
from ..exc import NotFoundError

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

    # TODO: work on Take functions

    @classmethod
    def get_all(cls, , project_id):
        from afd_dbserver.models.validators import TakeStatusValidator, TakeTypeValidator
        query = request.dbsession.query(cls).join(Project).filter(Project.id==project_id)
        if "omit_status" in request.params:
            omit_status_filters = request.params.getall("omit_status")
            for status in omit_status_filters:
                validator = TakeStatusValidator()
                status = validator.to_python(status)
                query = query.filter(cls.status!=status)
        if "type" in request.params:
            type_param = request.params.get("type")
            validator = TakeTypeValidator()
            type_ = validator.to_python(type_param)
            LOG.debug("Filtering by take type: %s"%type_)
            query = query.filter(cls.type_==type_)
        return query.order_by(cls.creation_date.desc()).all()

    @classmethod
    def get_by_name(cls, request, project_id, name):
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


