
import uuid
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, delete, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .resource_mixin import ResourceMixin
from .project import Project
from .note import Note, NoteAssoc
from .resource import Resource, ResourceAssoc
from .take_select_list import TakeSelectList, TakeSelectListAssoc

if TYPE_CHECKING:
    from .timecode_range import TimecodeRange
    from .capture_load import CaptureLoad
    from .take import Take

class TakeSelect(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ 
    """

    CLS_ID_ATTR: ClassVar = "take_select_id"
    __tablename__ = "take_select_t"
    __table_args__ = (UniqueConstraint(
        'take_id', 'timecode_range_id', name='take_select_take_timecode_range_uix'), 
    )
    delivery_name: Optional[str] = Field(max_length=128, default=None)
    description: Optional[str] = Field(default=None)
    priority: Optional[int] = Field(default=0, ge=0)
    is_editable: Optional[bool] = Field(default=True)
    take_id: uuid.UUID = Field(foreign_key="take_t.id", nullable=False)
    take: "Take" = Relationship(
        back_populates="take_selects",
        sa_relationship_kwargs={"lazy": "joined"}
    )
    # delivery_date: Optional[date] = Field(default=None)
    # delivered: Optional[bool] = Field(default=False)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="take_selects")
    capture_load_id: uuid.UUID = Field(
        foreign_key="capture_load_t.id", nullable=False)
    capture_load: "CaptureLoad" = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    timecode_range_id: uuid.UUID = Field(foreign_key="timecode_range_t.id")
    timecode_range: "TimecodeRange" = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    notes: list["Note"] = Relationship(
        link_model=NoteAssoc,
        back_populates="take_select",
        sa_relationship_kwargs={
            # "order_by": "note_t.last_modified.desc()",
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="take_select"
    )
    take_select_lists: list["TakeSelectList"] = Relationship(
        link_model=TakeSelectListAssoc,
        back_populates="take_selects",
        sa_relationship_kwargs={
            "lazy": "joined"
        }
    )

    @classmethod
    def delete_all_by_project(cls, dbsession, project_id):
        from .timecode_range import TimecodeRange
        stmt = (
            select(cls.timecode_range_id)
            .where(cls.project_id == project_id)
        )
        tc_ranges_ids = dbsession.exec(stmt).all()
        rows_affected = super(TakeSelect, cls).delete_all_by_project(dbsession, project_id)
        rows_affected += dbsession.exec(
            delete(TimecodeRange)
            .where(TimecodeRange.id.in_(tc_ranges_ids))
        ).count()
        dbsession.commit()
        return rows_affected

    @classmethod
    def create(
            cls,
            payload: SQLModel,
            dbsession: DBSession,
            enabled_entries_only=True
    ):
        from .capture_load import CaptureLoad
        from .timecode_range import TimecodeRange
        # Copy CaptureLoad
        src_cpl = CaptureLoad.get_by_id(payload.capture_load_id, dbsession)
        copied_cpl = src_cpl.copy_cpl(
            dbsession,
            enabled_entries_only=enabled_entries_only
        )
        payload.capture_load_id = copied_cpl.id
        # Copy TimecodeRange
        src_tcr = TimecodeRange.get_by_id(payload.timecode_range_id, dbsession)
        copied_tcr = src_tcr.copy_tc(dbsession)
        payload.timecode_range_id = copied_tcr.id
        model = super(TakeSelect, cls).create(payload, dbsession)
        return model

    # def delete(self, request):
    #     if request.authenticated_userid == self.created_by:
    #         request.dbsession.delete(self)
    #         self.capture_load.delete(request)
    #         self.timecode_range.delete(request)
    #         for note in self.notes:
    #             note.delete(request)
    #     else:
    #         raise HTTPForbidden("You can only delete your own TakeSelects. This was created by {0}.".format(self.created_by))

