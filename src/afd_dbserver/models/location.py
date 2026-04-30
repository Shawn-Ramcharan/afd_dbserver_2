from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlmodel import (
    SQLModel,
    Session,
    Field,
    select
)
from .mixin import BaseMixin, AttrMixin

class Location(BaseMixin, AttrMixin, SQLModel, table=True):
    """ A physical location where a shoot is happening.
    """
    __tablename__ = "location_t"
    code: str = Field(max_length=32, unique=True, nullable=False)
    name: str = Field(max_length=128)
    address: Optional[str]
    # sessions = relationship("Session", back_populates="location")

    @classmethod
    def get_all(cls, dbsession: Session):
        return dbsession.exec(select(cls).order_by(cls.code.asc())).all()

    @classmethod
    def get_by_code(cls, dbsession: Session, code: str):
        try:
            return dbsession.exec(select(cls).where(cls.code == code)).one()
        except NoResultFound:
            return None
