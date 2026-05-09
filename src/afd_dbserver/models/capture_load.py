import uuid
import logging
from typing import TYPE_CHECKING, Any, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
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
from ..exc import BadRequestError, NotFoundError
from .resource import Version

if TYPE_CHECKING:
    from .take import Take
    from .volume import Volume

LOG = logging.getLogger(__name__)

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
    def create(cls, payload: SQLModel, dbsession: DBSession):
        cls._check_single_owner(payload)
        model = super(CaptureLoad, cls).create(payload, dbsession)
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

    def update_tags(self, tags: list[str]):
        if self.tags is None:
            self.tags = []
        if self.LIVE in self.tags:
            tags.append(self.LIVE)
        self.tags = tags

    @classmethod
    def update(
        cls,
        id_: uuid.UUID,
        payload: SQLModel,
        dbsession: DBSession,
        is_live: bool = False
    ):
        cls._check_single_owner(payload)
        cpl_ = cls.get_by_id(id_, dbsession)
        if is_live is True:
            if cpl_.volume is None:
                raise BadRequestError(
                    "The 'live' tag can only be set on CaptureLoad objects owned by a Volume.")
            cpl_.set_as_live(dbsession)
        for field, value in payload.model_dump().items():
            if hasattr(payload, "attrs"):
                cpl_.merge_attrs(payload.attrs)
            elif hasattr(payload, "tags"):
                cpl_.update_tags(payload.tags)
            else:
                setattr(cpl_, field, value)
        cpl_.update_stamp(dbsession)
        dbsession.commit()
        dbsession.refresh(cpl_)
        return cpl_

    def copy_cpl(
        self,
        dbsession: DBSession,
        target_owner: Any,
        enabled_entries_only: bool = False
    ):
        # Get Current Attrs
        attrs = {}
        if self.attrs is not None:
            attrs = self.attrs.copy()
        attrs.update({"copied_from": str(self.id)})
        # Get Target Id
        take_id = None
        volume_id = None
        if target_owner is not None:
            if target_owner.__class__.__name__ == "Volume":
                volume_id = target_owner.id
            elif target_owner.__class__.__name__ == "Take":
                take_id = target_owner.id
        tags = self.tags or []
        if self.LIVE in tags:
            tags.remove(self.LIVE)
        payload = SQLModel(
            project_id=self.project.id,
            name=self.name,
            take_id=take_id,
            volume_id=volume_id,
            attrs=attrs,
            tags=tags,
            created_by="shawn",
            modified_by="shawn"
        )
        new_capture_load = self.__class__.create(payload, dbsession)
        # copy the entries
        for entry in self.entries:
            if enabled_entries_only is True and entry.is_enabled is False:
                continue
            entry.copy_cple(dbsession, new_capture_load)
        dbsession.commit()
        return new_capture_load

    # def delete_cpl(self, dbsession: DBSession):
    #     # LOG.debug("Deleting CaptureLoad: {0}".format(self.id))
    #     entries = reversed(self.entries)
    #     for entry in entries:
    #         entry.delete(request)
    #     dbsession.delete(self)

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
    solver_setup: "SolverSetup" = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(
        foreign_key="mapping_t.id", default=None)
    mapping: "Mapping" = Relationship()
    index: Optional[int] = Field(nullable=False, ge=1)
    is_enabled: Optional[bool] = Field(default=True)
    has_body: Optional[bool] = Field(default=True)
    has_facial: Optional[bool] = Field(default=False)
    has_fingers: Optional[bool] = Field(default=False)
    versions: list["CaptureLoadEntryVersion"] = Relationship(
        back_populates="capture_load_entry",
        # order_by="CaptureLoadEntryVersion.name.asc()",
    )

    @classmethod
    def get_next_index(cls, capture_load_id: uuid.UUID, dbsession: DBSession):
        stmt = select(CaptureLoadEntry).where(
            CaptureLoadEntry.capture_load_id == capture_load_id
        )
        index = dbsession.exec(stmt).count()
        return index

    @classmethod
    def create(cls, payload: SQLModel, dbsession: DBSession):
        index = cls.get_next_index(payload.capture_load_id, dbsession)
        payload.index = index
        model = super(CaptureLoadEntry, cls).create(payload, dbsession)
        return model

    def copy_cple(self, dbsession: DBSession, capture_load: CaptureLoad):
        attrs = {}
        if self.attrs is not None:
            attrs = self.attrs.copy()
        attrs.update({"copied_from": str(self.id)})
        payload = SQLModel(
            project_id=capture_load.project.id,
            capture_load_id=capture_load.id,
            solver_setup_id =self.solver_setup_id,
            mapping_id=self.mapping_id,
            index=self.index,
            is_enabled=self.is_enabled,
            has_body=self.has_body,
            has_fingers=self.has_fingers,
            has_facial=self.has_facial,
            attrs=attrs
        )
        copied_entry = self.__class__.create(payload, dbsession)
        # copy the associated versions
        for version in self.versions:
            version.copy_cplev(dbsession, copied_entry)
        return copied_entry

    # def update_(self, request, params):
    #      # check for index change
    #     if "index" in params:
    #         orig_index = self.index # 1
    #         target_index = params["index"] # 0
    #         entries = self.capture_load.entries
    #         if target_index>=len(entries):
    #             raise HTTPBadRequest("CaptureLoadEntry index is greater than entry list length: {0}>{1}".format(target_index,len(entries)))
    #         for entry in entries:
    #             if entry.id == self.id:
    #                 continue
    #             entry_index = entry.index
    #             if entry_index > orig_index:
    #                 # shift left
    #                 entry_index -= 1
    #             if entry_index >= target_index:
    #                 # shift right
    #                 entry_index += 1
    #             if entry_index != entry.index:
    #                 LOG.debug("Moving entry %d to %d (%s)"%(entry.index, entry_index, entry))
    #                 entry.index = entry_index
    #     # update attributes
    #     for key in params:
    #         if not hasattr(self, key):
    #             continue
    #         if key=="attrs":
    #             self.merge_attrs(params[key])
    #         else:
    #             LOG.debug("Setting {0} to {1}".format(key, params[key]))
    #             setattr(self, key, params[key])
    #     self.update_stamp(request)
    #     flag_dirty(self.capture_load)

    # def delete(self, request):
    #     LOG.debug("Deleting CaptureLoadEntry: {0}".format(self.id))
    #     indexToDelete = self.index
    #     self.index=-1
    #     # update indices of sibling entries
    #     for sibling in self.capture_load.entries:
    #         if sibling.index > indexToDelete:
    #             sibling.index -= 1
    #     versions = self.versions
    #     for version in versions:
    #         version.delete(request)
    #     request.dbsession.delete(self)

    def add_or_update_version(
        self,
        dbsession: DBSession,
        name: str,
        version: Any, # Should be Version
        attrs: dict
    ):
        paylaod = SQLModel(
            project_id=version.project.id,
            capture_load_entry_id=self.id,
            name=name,
            version_id=version.id,
            attrs=attrs
        )
        try:
            cle_version = self.get_version_by_name(dbsession, name)
            LOG.debug("Updating {0} record with id={1}".format(cle_version.__class__.__name__, cle_version.id))
            self.__class__.update(cle_version.id, paylaod, dbsession)
        except NotFoundError:
            cle_version = self.__class__.create(paylaod, dbsession)
            LOG.debug("Created new {0} record with id={1}".format(cle_version.__class__.__name__, cle_version.id))
        return cle_version

    def get_version_by_name(self, dbsession: DBSession, name: str):
        stmt = select(CaptureLoadEntryVersion).where(
            CaptureLoadEntryVersion.capture_load_entry_id == self.id,
            CaptureLoadEntryVersion.name == name
        )
        try:
            cle_version = dbsession.scalar(stmt).one()
            return cle_version
        except NoResultFound:
            raise NotFoundError(CaptureLoadEntryVersion, name=name, id=self.id)

    def remove_version(self, dbsession: DBSession, cle_version_id: uuid.UUID):
        LOG.debug('"{0}"'.format(cle_version_id))
        cle_version = CaptureLoadEntryVersion.get_by_id(cle_version_id, dbsession)
        LOG.debug(cle_version)
        if not cle_version:
            raise NotFoundError(CaptureLoadEntryVersion, id=self.id)
        LOG.debug("Removing {0} from {1}".format(cle_version, self))
        dbsession.delete(cle_version)
        dbsession.commit()

    def remove_version_by_name(self, dbsession: DBSession, name: str):
        cle_version = self.get_version_by_name(dbsession, name)
        LOG.debug("Removing {0} from {1}".format(cle_version, self))
        dbsession.delete(cle_version)
        dbsession.commit()

    def __repr__(self):
        return "<%s : %d. %s>"%(self.__class__.__name__, self.index, self.id)

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
    version: Version = Relationship()

    def copy_cplv(self, dbsession: DBSession, capture_load_entry: CaptureLoadEntry):
        payload = SQLModel(
            project_id=capture_load_entry.project.id,
            capture_load_entry_id=capture_load_entry.id,
            name=self.name,
            version_id=self.version.id,
            attrs=self.attrs
        )
        copied_cplev = self.__class__.create(payload, dbsession)
        dbsession.add(copied_cplev)
        dbsession.commit()
        return copied_cplev

    # def delete(self, request):
    #     LOG.debug("Deleting CaptureLoadEntryVersion: {0}".format(self.id))
    #     request.dbsession.delete(self)

