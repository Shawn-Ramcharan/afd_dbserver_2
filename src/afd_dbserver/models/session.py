import uuid
from typing import TYPE_CHECKING, Any, Optional, Self
from sqlalchemy.schema import UniqueConstraint
from datetime import date
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .resource_mixin import ResourceMixin
from .project import Project
from .location import Location
from .note import Note, NoteAssoc
from .resource import Resource, ResourceAssoc
from ..exc import InvalidEnumValueError
from .take import Take, ETakeType
if TYPE_CHECKING:
    from .volume import Volume

class Session(
    BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True
):
    """ """

    __tablename__ = "session_t"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "project_id",
            "location_id",
            name="session_name_project_location_uix",
        ),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    name: Optional[str] = Field(max_length=128, nullable=False, index=True)
    description: Optional[str] = Field(max_length=1024)
    shoot_date: Optional[date] = Field(default_factory=utcnow)
    timecode_rate: Optional[str] = Field(max_length=32)
    sample_rate: float = Field(ge=0.0)
    folder: Optional[str] = Field()
    location_id: uuid.UUID = Field(foreign_key="location_t.id", nullable=False)
    project: Project = Relationship(back_populates="sessions")
    location: Location = Relationship(back_populates="sessions")
    volumes: list["Volume"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={
            "order_by": "Volume.code.desc()",
            "lazy": "dynamic"
        }
    )
    takes: list["Take"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={
            "order_by": "Take.creation_date.desc()",
            "lazy": "dynamic"
        }
    )
    notes: list["Note"] = Relationship(
        link_model=NoteAssoc,
        back_populates="session",
        sa_relationship_kwargs={
            "order_by": "Note.last_modified.desc()",
            "lazy": "dynamic"
        }
    )
    resources: list[Resource] = Relationship(
        link_model=ResourceAssoc,
        back_populates="session",
    )

    @classmethod
    def create(cls, user_id: str, payload: Self, dbsession: DBSession):
        if payload.name is None:
            shoot_date = str(payload.shoot_date).replace("-", "")
            location = Location.get_by_id(payload.location_id, dbsession)
            results = cls.get_all(
                dbsession,
                payload.project_id,
                location_ids=[location.id,],
                shoot_dates=[payload.shoot_date,]
            )
            number = len(results) + 1
            payload.name = f"{shoot_date}_{location.code}_{number:02}"
        if payload.sample_rate is None:
            payload.sample_rate = 30
        if payload.timecode_rate is None:
            payload.timecode_rate = "TCRate_30"
        return super(Session, cls).create(user_id, payload, dbsession)

    @classmethod
    def get_all(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        location_ids: Optional[list[uuid.UUID]] = None,
        shoot_dates: Optional[list[date]] = None,
    ):
        sessions = select(cls).where(cls.project_id == project_id)
        # optional Location filter
        if location_ids is not None:
            sessions = sessions.where(cls.location_id.in_(location_ids))
        # optional date filter
        if shoot_dates is not None:
            sessions = sessions.where(cls.shoot_date.in_(shoot_dates))
        return dbsession.exec(sessions.order_by(cls.name)).all()

    @classmethod
    def get_all_dates(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        location_id: Optional[uuid.UUID] = None,
    ):
        sessions = select(cls.shoot_date).where(cls.project_id == project_id)
        # optional Location filter
        if location_id is not None:
            sessions = sessions.where(cls.location_id == location_id)
        records = dbsession.exec(sessions.distinct()).all()
        # return [i[0] for i in records]
        return [i for i in records]

    @classmethod
    def get_by_name(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        name: str,
        location_id: Optional[uuid.UUID] = None,
    ):
        sessions = select(cls).where(
            cls.project_id == project_id,
            cls.name == name
        )
        if location_id is not None:
            sessions = sessions.where(Session.location_id == location_id)
        return dbsession.exec(sessions).all()

    @classmethod
    def get_all_locations(cls, dbsession: DBSession, project_id: uuid.UUID):
        stmt = select(distinct(cls.location_id)).where(
            cls.project_id == project_id)
        location_ids = dbsession.exec(stmt).all()
        return [Location.get_by_id(loc_id, dbsession) for loc_id in location_ids]

    def get_takes(self, dbsession: DBSession, type_: Optional[ETakeType] = None, limit_: Optional[int] = None, offset_: Optional[int] = None):
        stmt = select(Take).where(Take.session_id==self.id)
        if type_ is not None:
            if type_.value not in ETakeType.__members__:
                raise InvalidEnumValueError(type_, ETakeType)
            stmt = stmt.where(Take.type_ == type_)
        if offset_ is not None:
            stmt = stmt.offset(offset_)
        if limit_ is not None:
            stmt = stmt.limit(limit_)
        return dbsession.exec(stmt.order_by(Take.creation_date.desc())).unique().all()
