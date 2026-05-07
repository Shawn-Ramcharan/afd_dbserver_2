import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Optional
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import ARRAY, Text
from sqlmodel import Session as DBSession
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
    Column,
    select
)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .project import Project
from ..exc import BadRequestError
if TYPE_CHECKING:
    from .take import Take
    from .volume import Volume


class CaptureLoad(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):

    LIVE: ClassVar = "live"

    __tablename__ = "capture_load_t"
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    name: str = Field(max_length=128)
    tags: Optional[list[str]] = Field(default=None, sa_column=Column('tags', ARRAY(Text())))
    volume_id: Optional[uuid.UUID] = Field(default=None, foreign_key="volume_t.id")
    volume: Optional["Volume"] = Relationship(back_populates="capture_loads")
    take_id: Optional[uuid.UUID] = Field(default=None, foreign_key="take_t.id")
    take: Optional["Take"] = Relationship(back_populates="capture_loads")
    entries: list["CaptureLoadEntry"] = Relationship(
        back_populates="capture_load",
        # order_by="CaptureLoadEntry.index.asc()"
    )

    @classmethod
    def create(cls, payload: SQLModel, dbsession: Session):
        cls._check_single_owner(payload)
        super(CaptureLoad, cls).create(payload, dbsession)
        return model

    @classmethod
    def _check_single_owner(cls, payload: SQLModel):
        if payload.volume_id is not None and payload.take_id is not None:
            raise BadRequestError("A CaptureLoad can be linked to a Volume OR a Take.")

    @classmethod
    def get_capture_loads_by_tags(
        cls,
        dbsession: DBSession,
        owner: Any,
        tags: list[str]
    ):
        if owner.__class__.__name__ == "Volume":
            stmt = select(CaptureLoad).where(
                CaptureLoad.volume_id == owner.id,
                CaptureLoad.tags.contains(tags)
            )
        elif owner.__class__.__name__ == "Take":
            stmt = select(CaptureLoad).where(
                CaptureLoad.take_id == owner.id,
                CaptureLoad.tags.contains(tags)
            )
        else:
            raise RuntimeError("Unhandled owner")
        return dbsession.exec(stmt).all()

    def set_as_live(self, dbsession: DBSession):
        if self.volume_id is None:
            return
        if self.tags is None:
            self.tags = []
        for capture_load in CaptureLoad.get_capture_loads_by_tags(dbsession, self.volume, [self.LIVE]):
            if capture_load.tags is None:
                continue
            if self.LIVE in capture_load.tags:
                # remove the 'live' tag from this version
                capture_load.tags.remove(self.LIVE)
        self.tags.append(self.LIVE)
        dbsession.commit()

    def update_tags(self, dbsession: DBSession, tags: list[str]):
        if self.tags is None:
            self.tags = []
        if self.LIVE in self.tags:
            tags.append(self.LIVE)
        self.tags = tags
        dbsession.commit()

    # TODO: Update the rest of Capture load functions

    def update(self, request, params):
        self.__check_single_owner(params)
        if "is_live" in params:
            if self.volume_id is None:
                raise HTTPBadRequest("The 'live' tag can only be set on CaptureLoad objects owned by a Volume.")
            self.set_as_live(request)
            del params["is_live"]
        # update attributes
        for key in params:
            if not hasattr(self, key):
                continue
            if key=="attrs":
                self.merge_attrs(params[key])
            elif key=="tags":
                self.update_tags(params[key])
            else:
                if key == "take_id":
                    self.volume = None
                elif key == "volume_id":
                    self.take = None
                setattr(self, key, params[key])
        self.update_stamp(request)

    def copy_cpl(self, request, target, enabled_entries_only=False):
        if self.attrs is not None:
            attrs = copy.deepcopy(self.attrs)
        else:
            attrs = {}
        attrs["copied_from"] = str(self.id)
        kwargs = {
            "project":self.project,
            "name":self.name,
            "volume_id":None,
            "take_id":None,
            "attrs":attrs
        }
        if target is not None:
            if target.__class__.__name__ == "Volume":
                kwargs["volume_id"] = target.id
            elif target.__class__.__name__ == "Take":
                kwargs["take_id"] = target.id
        new_capture_load = self.__class__(**kwargs)
        new_capture_load.set_creation_stamp(request)
        if new_capture_load.attrs:
            new_capture_load.attrs.update({"copied_from":str(self.id)})
        else:
            new_capture_load.attrs = {"copied_from":str(self.id)}
        # copy the tags, but not the "live" tag.  This has special meaning for the stage.
        tags = self.tags
        if 'live' in tags:
            tags.remove("live")
        new_capture_load.tags = tags
        request.dbsession.add(new_capture_load)
        request.dbsession.flush()
        # copy the entries
        for entry in self.entries:
            if enabled_entries_only:
                if entry.is_enabled:
                    entry.copy(request, new_capture_load)
            else:
                entry.copy(request, new_capture_load)
        request.dbsession.flush()
        return new_capture_load


class CaptureLoadEntry(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    __tablename__ = "capture_load_entry_t"
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    capture_load_id: uuid.UUID = Field(
        foreign_key="capture_load_t.id", nullable=False)
    capture_load: "CaptureLoad" = Relationship(back_populates="entries")
    solver_setup_id: Optional[uuid.UUID] = Field(
        foreign_key="solver_setup_t.id", default=None
    )
    solver_setup: Optional["SolverSetup"] = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(
        foreign_key="mapping_t.id", default=None)
    mapping: Optional["Mapping"] = Relationship()
    index: Optional[int] = Field(nullable=False, ge=1)
    is_enabled: Optional[bool] = Field(default=True)
    has_body: Optional[bool] = Field(default=True)
    has_facial: Optional[bool] = Field(default=False)
    has_fingers: Optional[bool] = Field(default=False)
    versions: Optional[list["CaptureLoadEntryVersion"]] = Relationship(
        back_populates="capture_load_entry",
        # order_by="CaptureLoadEntryVersion.name.asc()",
    )


class CaptureLoadEntryVersion(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    __tablename__ = "capture_load_entry_version_t"
    __table_args__ = (UniqueConstraint(
        "name",
        "capture_load_entry_id",
        "version_id",
        name="capture_load_entry_version_name_capture_load_id_version_id_uix",
    ),)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    name: str = Field(max_length=64)
    capture_load_entry_id: uuid.UUID = Field(
        foreign_key="capture_load_entry_t.id", nullable=False
    )
    capture_load_entry: "CaptureLoadEntry" = Relationship(
        back_populates="versions",
        #order_by="CaptureLoadEntryVersion.name.asc()"
    )
    version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    version: "Version" = Relationship()
