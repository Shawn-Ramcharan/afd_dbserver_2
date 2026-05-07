import uuid
import logging
import enum
from typing import TYPE_CHECKING, Any, ClassVar, Optional
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import Enum as SqlaEnum
from sqlalchemy import ARRAY, Text
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, Column, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from ..exc import NotFoundError

if TYPE_CHECKING:
    from .mapping import Mapping

LOG = logging.getLogger(__name__)

class EVirtualAssetType(enum.Enum):
    character = "character"
    prop = "prop"
    scene = "scene"
    camera = "camera"


class VirtualAsset(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    __tablename__ = "virtual_asset_t"
    __table_args__ = (
        UniqueConstraint("code", "project_id",
        name="virtual_asset_code_project_uix"),
    )
    code: str = Field(max_length=32, nullable=False)
    client_name: Optional[str] = Field(max_digits=128, default=None)
    type_: EVirtualAssetType = Field(
        sa_column=Column(SqlaEnum(EVirtualAssetType, name='evirtualassettype'), nullable=False)
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="virtual_assets")
    revisions: list["VirtualAssetRevision"] = Relationship(
        # order_by="desc(VirtualAssetRevision.number)",
        back_populates="virtual_asset",
    )

    def get_revision(self, dbsession: DBSession, number):
        stmt = select(VirtualAssetRevision).where(
            VirtualAssetRevision.virtual_asset_id == self.id,
            VirtualAssetRevision.number == number
        )
        try:
            return dbsession.exec(stmt).one()
        except NoResultFound:
            raise NotFoundError(
                f"No revision with number={number} found for VirtualAsset id={self.id}")

    def get_next_logical_number(self, dbsession: DBSession):
        """ Returns the next available version number.
        """
        stmt = (select(VirtualAssetRevision.number)
                .where(VirtualAssetRevision.virtual_asset_id == self.id)
                )
        results = dbsession.exec(stmt).all()
        try:
            return max(results)+1
        except ValueError:
            return 1

    def get_all_with_tags(self, dbsession: DBSession, tags: list[str]):
        # tags must be a list!
        stmt = select(VirtualAssetRevision).where(
            VirtualAssetRevision.virtual_asset_id == self.id,
            VirtualAssetRevision.tags.contains(tags)
        )
        try:
            dbsession.exec(stmt).all()
        except NoResultFound as err:
            LOG.debug(err)
            return []

class VirtualAssetRevision(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    OFFICIAL: ClassVar = "official"
    CLS_ID_ATTR: ClassVar = "virtual_asset_revision_id"

    __tablename__ = "virtual_asset_revision_t"
    __table_args__ = (
        UniqueConstraint(
            "virtual_asset_id",
            "number",
            name="virtual_asset_revision_virtual_asset_id_number_uix",
        ),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    number: int = Field(nullable=False, ge=1)
    tags: Optional[list[str]] = Field(default=None, default_factory=list)#sa_column=Column('tags', ARRAY(Text())))
    virtual_asset_id: uuid.UUID = Field(foreign_key="virtual_asset_t.id", nullable=False)
    virtual_asset: VirtualAsset = Relationship(
        back_populates="revisions",
        sa_relationship_kwargs=dict(lazy="joined")
    )
    source_mappings: list["Mapping"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={
            "primaryjoin": "VirtualAssetRevision.id==Mapping.source_id"
        }
    )
    target_mappings: list["Mapping"] = Relationship(
        back_populates="target",
        sa_relationship_kwargs={
            "primaryjoin": "VirtualAssetRevision.id==Mapping.target_id"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="virtual_asset_revision"
    )

    def set_as_official(self, dbsession: DBSession):
        for revision in self.virtual_asset.get_all_with_tags(dbsession, [self.OFFICIAL]):
            if self.OFFICIAL in revision.tags:
                # remove the 'official' tag from this version
                tags = revision.tags
                tags.remove(self.OFFICIAL)
                revision.tags = tags
        if self.tags is None:
            self.tags = []
        self.tags.append(self.OFFICIAL)
        dbsession.commit()

    def update_tags_and_attrs(
        self,
        dbsession: DBSession,
        tags: list[str] | None = None,
        attrs: dict[str, Any] | None = None
    ):
        if self.tags is None:
            self.tags = []
        if tags is not None:
            for tag in tags:
                if tag in self.tags:
                    continue
                self.tags.append(tag)
        if attrs is not None:
            self.merge_attrs(attrs)
        self.update_stamp(dbsession)
        dbsession.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} : {self.number}. {self.id}>"
