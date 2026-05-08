import uuid
import enum
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy import Enum as SqlaEnum
from sqlmodel import (SQLModel, Field, Relationship, Column)
from .mixin import IdMixin, BaseMixin, AttrMixin, ProjectScopedDataMixin, ProjectScopedAssocMixin
from .project import Project

if TYPE_CHECKING:
    from .take import Take
    from .take_select import TakeSelect
    from .session import Session

class NoteAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "note_assoc_t"
    note_id: uuid.UUID = Field(
        foreign_key="note_t.id", unique=True, nullable=False)
    note: "Note" = Relationship()
    session_id: Optional[uuid.UUID] = Field(foreign_key="session_t.id", default=None)
    session: Optional["Session"] = Relationship()
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id", default=None)
    take: Optional["Take"] = Relationship()
    take_select_id: Optional[uuid.UUID] = Field(foreign_key="take_select_t.id", default=None)
    take_select: Optional["TakeSelect"] = Relationship()


class ENoteType(enum.Enum):
    stage = "stage"
    post = "post"
    client = "client"


class Note(
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    SQLModel,
    table=True,
):
    """ """

    __tablename__ = "note_t"
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    text: Optional[str] = Field(default=None)
    author: Optional[str] = Field(max_length=128, default=None)
    type_: ENoteType = Field(
        sa_column=Column(SqlaEnum(ENoteType, name="enoteype"), nullable=False)
    )
    session: "Session" = Relationship(
        link_model=NoteAssoc,
        back_populates="notes"
    )
    take: "Take" = Relationship(
        link_model=NoteAssoc,
        back_populates="notes"
    )
    take_select: "TakeSelect" = Relationship(
        link_model=NoteAssoc,
        back_populates="notes"
    )
    PROJECT_ASSOC_CLS: ClassVar = NoteAssoc
