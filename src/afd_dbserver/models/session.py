import uuid
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime
from sqlmodel import Session as DbSession
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
    select
)
from .mixin import BaseMixin, AttrMixin, utcnow
from .project import Project
from .location import Location

class Session(BaseMixin, AttrMixin, SQLModel, table=True): #ResourceMixin, ProjectScopedDataMixin):
    """
    """
    __tablename__ = "session_t"
    __table_args__ = (UniqueConstraint(
        'name',
        'project_id',
        'location_id',
        name='session_name_project_location_uix'
    ),)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="sessions")
    name: str = Field(max_length=128, nullable=False, index=True)
    description: str = Field(max_length=1024)
    shoot_date: datetime = Field(default_factory=utcnow)  # should be stored in timezone=UTC
    timecode_rate: str = Field(max_length=32)
    sample_rate: float
    folder: str
    location_id: uuid.UUID = Field(foreign_key="location_t.id", nullable=False)
    location: Location = Relationship(back_populates="sessions")
    # volumes = relationship("Volume", back_populates="session", order_by=desc(text("volume_t.code")))
    # takes = relationship("Take", back_populates="session", order_by=desc(text("take_t.creation_date")))
    # notes = relationship("Note", secondary="note_assoc_t", order_by=desc(text("note_t.last_modified")) )
    # resources = relationship("Resource", secondary="resource_assoc_t", backref=backref("sessions", overlaps="session"), overlaps="session")

    # @classmethod
    # def get_all(cls, request, project, location_ids=None, shoot_dates=None):
    #     query = request.dbsession.query(cls).filter(cls.project_id==project.id)
    #     # optional Location filter
    #     if location_ids is not None:
    #         query = query.filter(Session.location_id.in_(location_ids))
    #     # optional date filter
    #     if shoot_dates is not None:
    #         query = query.filter(Session.shoot_date.in_(shoot_dates))
    #     return query.order_by(Session.name).all()
    #
    # @classmethod
    # def get_all_dates(cls, request, project, location_id=None):
    #     query = request.dbsession.query(cls.shoot_date).filter(cls.project_id==project.id)
    #     # optional Location filter
    #     if location_id is not None:
    #         query = query.filter(cls.location_id==location_id)
    #     records = query.distinct().all()
    #     return [i[0] for i in records]
    #
    # @classmethod
    # def get_by_name(cls, request, project, name, location_id=None):
    #     query = request.dbsession.query(cls).filter(and_(cls.project_id==project.id, cls.name==name))
    #     if location_id is not None:
    #         query = query.filter(Session.location_id==location_id)
    #     return query.all()
    #
    # @classmethod
    # def get_all_locations(cls, request, project_id):
    #     location_ids = [l[0] for l in request.dbsession.query(distinct(cls.location_id)).filter(cls.project_id==project_id).all()]
    #     return [Location.get_by_id(request, location_id) for location_id in location_ids]
    #
    # def get_takes(self, request, type_=None):
    #     from .take import Take
    #     query = request.dbsession.query(Take).filter(Take.session_id==self.id)
    #     if type_ is not None:
    #         query = query.filter(Take.type_==type_)
    #     return query.order_by(Take.creation_date.desc()).all()
