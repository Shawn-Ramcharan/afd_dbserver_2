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
from .location import Location
if TYPE_CHECKING:
    from .volume import Volume
    from .take import Take
    from .note import Note
    from .resource import Resource


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
    description: str = Field(max_length=1024)
    # NOTE: Change to date object later!!
    shoot_date: datetime = Field(
        default_factory=utcnow
    )  # should be stored in timezone=UTC
    timecode_rate: str = Field(max_length=32)
    sample_rate: float = Field(default=30.0, ge=0.0)
    folder: str = Field()
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
        back_populates="note_assoc_t",
        # order_by="Note.last_modified.desc()"
    )  # , order_by=desc(text("note_t.last_modified")) )
    resources: list["Resource"] = Relationship(
        back_populates="sessions",
        # link_model="resource_assoc_t"
    )


    @classmethod
    def get_all(
        cls,
        dbsession: DbSession,
        project: Project,
        location_ids: Optional[list[uuid.UUID]] = None,
        shoot_dates: Optional[list[datetime]] = None,
    ):
        sessions = select(cls).where(cls.project_id == project.id)
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
        dbsession: DbSession,
        project: Project,
        location_id: Optional[uuid.UUID] = None,
    ):
        sessions = select(cls.shoot_date).where(cls.project_id == project.id)
        # optional Location filter
        if location_id is not None:
            sessions = sessions.where(cls.location_id == location_id)
        records = dbsession.exec(sessions.distinct()).all()
        # return [i[0] for i in records]
        return [i for i in records]

    @classmethod
    def get_by_name(
        cls,
        dbsession: DbSession,
        project: Project,
        name: str,
        location_id: Optional[uuid.UUID] = None,
    ):
        sessions = (
            select(cls).where(cls.project_id ==
                              project.id).where(cls.name == name)
        )
        if location_id is not None:
            sessions = sessions.where(Session.location_id == location_id)
        return dbsession.exec(sessions).all()

    @classmethod
    def get_all_locations(cls, dbsession: DbSession, project_id: uuid.UUID):
        query = select(distinct(cls.location_id)).where(
            cls.project_id == project_id)
        location_ids = dbsession.exec(query).scalars().all()
        return [Location.get_by_id(loc_id) for loc_id in location_ids]

    # def get_takes(self, request, type_=None):
    #     from .take import Take
    #     query = request.dbsession.query(Take).filter(Take.session_id==self.id)
    #     if type_ is not None:
    #         query = query.filter(Take.type_==type_)
    #     return query.order_by(Take.creation_date.desc()).all()


# class Volume(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin):
#     """ """
#
#     __tablename__ = "volume_t"
#     __table_args__ = (
#         UniqueConstraint("code", "session_id", name="volume_code_session_uix"),
#     )
#     project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
#     project: Optional[Project] = Relationship()
#     code: uuid.UUID = Field(max_length=32, nullable=False)
#     session_id: uuid.UUID = Field(foreign_key="session_t.id", nullable=False)
#     session: Optional[Session] = Relationship(back_populates="volumes")
#     devices: list[Device] = Relationship(
#         back_populates="volume", order_by="Device.code.asc()"
#     )
#     capture_loads: list[CaptureLoad] = Relationship(
#         back_populates="volume",
#         order_by=desc(text("capture_load_t.creation_date")),
#     )
#     resources: list[Resource] = Relationship(
#         link_model="resource_assoc_t", back_populates="volume"
#     )
