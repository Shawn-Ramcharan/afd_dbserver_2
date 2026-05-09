import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .resource_mixin import ResourceMixin
from .project import Project
from .location import Location
from .note import Note, NoteAssoc
from .resource import Resource, ResourceAssoc
from ..exc import BadRequestError
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
    project: Optional[Project] = Relationship(back_populates="sessions")
    name: str = Field(max_length=128, nullable=False, index=True)
    description: Optional[str] = Field(default=None, max_length=1024)
    shoot_date: Optional[date] = Field(
        default_factory=utcnow
    )  # should be stored in timezone=UTC
    timecode_rate: Optional[str] = Field(default="TCRate_30", max_length=32)
    sample_rate: float = Field(default=30.0, ge=0.0)
    folder: Optional[str] = Field(default=None)
    location_id: uuid.UUID = Field(foreign_key="location_t.id", nullable=False)
    location: Optional[Location] = Relationship(back_populates="sessions")
    volumes: list["Volume"] = Relationship(
        back_populates="session",
        # order_by="Volume.code.desc()"
    )  # order_by=desc(text("volume_t.code")))
    takes: list["Take"] = Relationship(
        back_populates="session",
        # order_by="Take.creation_date.desc()"
    )  # , order_by=desc(text("take_t.creation_date")))
    notes: list["Note"] = Relationship(
        link_model=NoteAssoc,
        back_populates="session",
        # order_by="Note.last_modified.desc()"
    )  # , order_by=desc(text("note_t.last_modified")) )
    resources: list[Resource] = Relationship(
        link_model=ResourceAssoc,
        back_populates="session",
        # link_model="resource_assoc_t"
    )


    @classmethod
    def get_all(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        location_ids: Optional[list[uuid.UUID]] = None,
        shoot_dates: Optional[list[datetime]] = None,
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

    def get_takes(self, dbsession: DBSession, type_: ETakeType | None = None):
        stmt = select(Take).where(Take.session_id==self.id)
        if type_ is not None:
            if type_ not in ETakeType.__members__:
                raise BadRequestError(f"{type_} is not a valid Take Type")
            stmt = stmt.where(Take.type_ == type_)
        return dbsession.exec(stmt.order_by(Take.creation_date.desc())).all()
