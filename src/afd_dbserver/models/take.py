import uuid
import enum
from typing import TYPE_CHECKING, Optional, Self
from sqlalchemy import Enum as SqlaEnum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import ARRAY, Text
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Field, Column, select, not_, distinct)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from .note import Note, NoteAssoc
from ..exc import NotFoundError, BadRequestError, InvalidEnumValueError

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
    slate: Optional[str] = Field(max_length=128, nullable=False)
    number: Optional[int] = Field(nullable=False, default=1, ge=1)
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
            "order_by": "CaptureLoad.creation_date.desc()"
        }
    )
    timecode_ranges: list["TimecodeRange"] = Relationship(
        back_populates="take",
        sa_relationship_kwargs={
            "lazy": "joined",
            "order_by": "TimecodeRange.creation_date.desc()",
        }
    )
    notes: list["Note"] = Relationship(
        back_populates="take",
        link_model=NoteAssoc,
        sa_relationship_kwargs={
            "order_by": "Note.last_modified.desc()"
        }
    )
    take_selects: list["TakeSelect"] = Relationship(
        back_populates="take",
        sa_relationship_kwargs={
            "lazy": "dynamic",
            "order_by": "TakeSelect.creation_date.desc()"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="take"
    )

    @classmethod
    def create(cls, user_id: str, payload: Self, dbsession: DBSession):
        name = payload.name
        token_idx = name.rfind("_")
        slate = name[:token_idx]
        try:
            number = int(name[token_idx+1:].replace("tk",""))
        except ValueError:
            raise BadRequestError(f"Unable to extract take number from name: {name}."
                "Should end with _tk## suffix.")
        payload.number = number
        payload.slate = slate
        model = super(Take, cls).create(user_id, payload, dbsession)
        return model

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
            for status_ in omit_status:
                if status_.value not in ETakeStatus.__members__:
                    raise InvalidEnumValueError(status_, ETakeStatus)
            stmt = stmt.where(not_(cls.status.in_(omit_status)))
        if type_:
            if type_ not in ETakeType.__members__:
                raise InvalidEnumValueError(type_, ETakeType)
            stmt = stmt.where(cls.type_ == type_)
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
            stmt = select(cls).where(
                cls.project_id == project_id,
                cls.name == name
            )
            return dbsession.exec(stmt).one()
        except NoResultFound:
            raise NotFoundError(cls, project_id=project_id, name=name)

    @classmethod
    def get_by_slates(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        slates: list[str]
    ):
        stmt = select(cls).where(
            cls.project_id == project_id,
            cls.slate.in_(slates)
        )
        return dbsession.exec(stmt.order_by(cls.name.desc())).all()

    @classmethod
    def get_all_slates(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        take_types: Optional[ETakeType] = None
    ):
        stmt = select(distinct(cls.slate)).where(cls.project_id == project_id)
        if take_types is not None:
            stmt = stmt.where(cls.type_.in_(take_types))
        return dbsession.exec(stmt).all()

    @classmethod
    def get_next_take_from_slate(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        slate: str
    ):
        stmt = select(cls.number).where(
            cls.project_id == project_id,
            cls.slate == slate
        )
        results = dbsession.exec(stmt).all()
        if len(results) == 0:
            return 1
        highest_value = max(results)
        return highest_value+1
