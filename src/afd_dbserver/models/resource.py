import uuid
import logging
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import ARRAY, Text, String
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Column, Field, Relationship, distinct, select)
from .mixin import (
    IdMixin,
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    ProjectScopedParentMixin,
    utcnow,
)
from ..exc import NotFoundError

LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .project import Project
    from .volume import Volume
    from .session import Session
    from .take import Take
    from .mapping import Mapping
    from .solver_setup import SolverSetup
    from .take_select import TakeSelect
    from .device import Device
    from .virtual_asset import VirtualAssetRevision


class ResourceAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "resource_assoc_t"
    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", unique=True)
    resource: "Resource" = Relationship()
    # =======================
    # NOTE: this is not for saying this resource is
    # project scoped. this is just for associating
    # resource to the project since projects can have
    # resources against it. Treat this attr/relationship
    # like any other attrs in the table like solver_setup_id,
    # mapping_id, etc.
    project_id: Optional[uuid.UUID] = Field(foreign_key="project_t.id", default=None)
    project: "Project" = Relationship()
    # =======================
    solver_setup_id: Optional[uuid.UUID] = Field(foreign_key="solver_setup_t.id", default=None)
    solver_setup: "SolverSetup" = Relationship()
    virtual_asset_revision_id: Optional[uuid.UUID] = Field(
        foreign_key="virtual_asset_revision_t.id",
        default=None
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(foreign_key="mapping_t.id", default=None)
    mapping: "Mapping" = Relationship()
    session_id: Optional[uuid.UUID] = Field(foreign_key="session_t.id", default=None)
    session: "Session" = Relationship()
    volume_id: Optional[uuid.UUID] = Field(foreign_key="volume_t.id", default=None)
    volume: "Volume" = Relationship()
    device_id: Optional[uuid.UUID] = Field(foreign_key="device_t.id", default=None)
    device: "Device" = Relationship()
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id", default=None)
    take: "Take" = Relationship()
    take_select_id: Optional[uuid.UUID] = Field(foreign_key="take_select_t.id", default=None)
    take_select: "TakeSelect" = Relationship()

class Resource(
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    SQLModel,
    table=True,
):
    __tablename__ = "resource_t"
    name: str = Field(max_length=64, nullable=False)
    group: str = Field(max_length=64, nullable=False)
    uri: Optional[str] = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: "Project" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    versions: list["Version"] = Relationship(
        back_populates="resource"
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    mapping: "Mapping" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    session: "Session" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    solver_setup: "SolverSetup" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    device: "Device" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    take: "Take" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    take_select: "TakeSelect" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    volume: "Volume" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )

    PROJECT_ASSOC_CLS: ClassVar = ResourceAssoc

    @classmethod
    def get_group_names(cls, dbsession: DBSession):
        data_ = dbsession.exec(select(distinct(cls.group))).all()
        return [r[0] for r in data_ if r is not None]

    def get_owner(self, dbsession: DBSession):
        """ Finds the owning class of this resource.  This is a bit convoluted because many 
        classes can have resources.
        """
        ID_TO_CLASS = {
            "project_id": Project,
            "volume_id": Volume,
            "session_id": Session,
            "take_id": Take,
            "mapping_id": Mapping,
            "solver_setup_id": SolverSetup,
            "take_select_id": TakeSelect,
            "device_id": Device,
            "virtual_asset_revision_id": VirtualAssetRevision,
        }
        try:
            stmt = select(ResourceAssoc).where(ResourceAssoc.resource_id == self.id)
            rsc_assoc_entry = dbsession.exec(stmt).one()
        except NoResultFound:
            raise NoResultFound(cls, id=self.id)
        for owner_id_attr, class_ in ID_TO_CLASS.items():
            owner_id = getattr(rsc_assoc_entry, owner_id_attr, None)
            if owner_id is not None:
                return class_.get_by_id(owner_id, dbsession)
        return None

    def get_versions(self, dbsession: DBSession, committed: bool = True):
        stmt = select(Version).where(Version.resource_id == self.id)
        if committed is True:
            stmt = stmt.where(Version.is_committed == True)
        return dbsession.exec(stmt.order_by(Version.number.desc())).all()

    def create_next_version(
        self,
        dbsession: DBSession,
        user_id: str,
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
        attrs: Optional[dict] = None
    ):
        # create the next logical version and add the items
        number = self.get_next_version_number(dbsession)
        LOG.debug(f"Creating version {number=} for resource {self.id}")
        uri = f"{self.uri}/version/{number}"
        payload = Version(
            project_id=self.project_id,
            resource_id=self.id,
            number=number,
            tags=tags,
            attrs=attrs,
            description=description,
            uri=uri,
            created_by=user_id,
            modified_by=user_id
        )
        version = Version.create(user_id, payload, dbsession)
        LOG.debug(f"Created version with {version.id=}")
        return version

    def get_next_version_number(self, dbsession: DBSession):
        """ Returns the next available version number.
        """ 
        stmt = select(Version.number).where(Version.resource_id==self.id)
        results = dbsession.exec(stmt).all()
        if len(results) == 0:
            return 1
        return max(results)

    def get_by_number(self, dbsession: DBSession, number: int):
        try:
            stmt = select(Version).where(
                Version.resource_id == self.id,
                Version.number == number
            )
            return dbsession.exec(stmt).one()
        except NoResultFound as err:
            return None

    def get_all_with_tags(self, dbsession: DBSession, tags: list[str]):
        stmt = select(Version).where(
            Version.resource_id == self.id,
            Version.tags.contains(tags),
            Version.is_committed is True
        )
        return dbsession.exec(stmt).all()

    def get_official_version(self, dbsession: DBSession):
        try:
            stmt = select(Version).where(
                Version.resource_id == self.id,
                Version.tags.contains([Version.OFFICIAL,]),
                Version.is_committed is True
            )
            return dbsession.exec(stmt).one()
        except NoResultFound as err:
            return None

    def get_latest_version(self, dbsession: DBSession):
        try:
            stmt = select(Version).where(
                Version.resource_id == self.id,
                Version.tags.contains([Version.LATEST,]),
                Version.is_committed is True
            )
            return dbsession.exec(stmt).one()
        except NoResultFound as err:
            return None

    def get_official_or_latest_version(self, dbsession: DBSession):
        LOG.debug("Looking for official version")
        version = self.get_official_version(dbsession)
        if version is None:
            LOG.debug("Looking for latest version")
            version = self.get_latest_version(dbsession)
        return version

    # def update(self, request, name=None, group=None, attrs=None):
    #     if name:
    #         self.name = name
    #     if group:
    #         self.group = group
    #     self.merge_attrs(attrs)
    #     self.update_stamp(request)
    #
    # def delete(self, request):
    #     # first delete versions
    #     for version in self.versions:
    #         version.delete(request)
    #     LOG.debug("Deleting %s"%self)
    #     request.dbsession.delete(self)

class Version(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):

    LATEST: ClassVar = "latest"
    OFFICIAL: ClassVar = "official"

    __tablename__ = "version_t"
    number: Optional[int] = Field(ge=1)
    tags: Optional[list[str]] = Field(default=None, sa_column=Column('tags', ARRAY(Text())))
    description: Optional[str] = Field(max_length=1024, default=None)
    is_committed: Optional[bool] = Field(default=False)
    uri: Optional[str] = Field(max_length=256)
    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", nullable=False)
    resource: Resource = Relationship(back_populates="versions")
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: "Project" = Relationship()
    # outgoing_links: list["VersionLink"] = Relationship(
    #     back_populates="from_version",
    #     # foreign_key="from_version_id"
    #     # link_model=VersionLink,
    #     sa_relationship_kwargs={
    #         "foreign_keys": ["from_version_id"],
    #     }
    # )
    # incoming_links: list["VersionLink"] = Relationship(
    #     back_populates="to_version",
    #     # foreign_keys=["to_version_id"]
    #     # link_model=VersionLink,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["to_version_id"],
    #     }
    # )

    def commit(self, dbsession: DBSession):
        if self.is_committed:
            return
        # transfer the 'latest' tag to this version
        for version in self.resource.get_all_with_tags(dbsession, [Version.LATEST,]):
            if version.id == self.id:
                continue
            if version.tags is None:
                continue
            if Version.LATEST in version.tags:
                # remove the 'latest' tag from this version
                LOG.debug(f"Removing latest tag from version {version.number}")
                tags = version.tags
                tags.remove(self.LATEST)
                version.tags = tags
        if self.tags is None:
            self.tags = []
        self.tags.append(self.LATEST)
        self.is_committed = True
        LOG.debug(f"Committing version ({self.id}) and setting latest {self.tags=}")
        dbsession.commit()

    def set_as_official(self, dbsession: DBSession):
        for version in self.resource.get_all_with_tags(dbsession, [Version.OFFICIAL]):
            if version.tags is None:
                continue
            if Version.OFFICIAL in version.tags:
                if version.tags is None:
                    continue
                # remove the 'official' tag from this version
                tags = version.tags
                tags.remove(self.OFFICIAL)
                version.tags = tags
        if self.tags is None:
            self.tags = []
        self.tags.append(self.OFFICIAL)
        dbsession.commit()

    # def update(self, request, tags=None, description=None, attrs=None):
    #     LOG.debug("Update: current tags are %s.\nAdd %s"%(self.tags, tags))
    #     if tags is not None:
    #         original_tags = self.tags
    #         self.tags=tags
    #         if self.OFFICIAL in original_tags:
    #             tags = self.tags + [self.OFFICIAL]
    #             self.tags = tags
    #         if self.LATEST in original_tags:
    #             tags = self.tags + [self.LATEST]
    #             self.tags = tags
    #         flag_modified(self, "tags")
    #     LOG.debug("Updated tags are: %s"%self.tags)
    #     if description is not None:
    #         LOG.debug("Updating description to: %s"%description)
    #         self.description = description
    #     self.merge_attrs(attrs)
    #     self.update_stamp(request)

    def add_item(
        self, dbsession: DBSession,
        user_id: str,
        name: str,
        location: str,
        attrs: Optional[dict] = None
    ):
        pass
        # item = Item(location=location)
        # item_count = request.dbsession.query(Item).filter(Item.location_hash==item.location_hash).count()
        # if item_count == 1:
        #     LOG.info("An item already exists with this location. Merging metadata: %s"%location)
        #     item = request.dbsession.query(Item).filter(Item.location_hash==item.location_hash).one()
        #     item.merge_attrs(attrs)
        #     item.modified_by = request.authenticated_userid
        # elif item_count > 1:
        #     LOG.critical("Integrity error!  More than one item record with same hash: %s (%s)"%(location, item.location_hash))
        #     raise Exception("Integrity error!  More than one item record with same hash: %s (%s)"%(location, item.location_hash))
        # else:
        #     request.dbsession.add(item)
        #     request.dbsession.flush()
        # # This will raise an IntegrityError constraint exception if name is already used - caught by view
        # uri = "%s?item=%s"%(self.uri,name)
        # item_assoc = ItemAssoc(name=name, version=self, item=item, uri=uri)
        # request.dbsession.add(item_assoc)
        # request.dbsession.flush()
        # return item_assoc

    def get_items(self, dbsession: DBSession):
        stmt = select(ItemAssoc, Item).where(
            ItemAssoc.version_id == self.id,
        )
        return dbsession.exec(stmt).all()

    def get_items_by_name(self, dbsession: DBSession, names: list[str]):
        """ Supports querying multiple items in the same query
        """
        stmt = select(ItemAssoc).where(
            ItemAssoc.version_id == self.id,
            ItemAssoc.name.in_(names)
        )
        return dbsession.exec(stmt).all()

    # def delete(self, request):
    #     # first delete items
    #     for item_assoc in self.get_items(request):
    #         item_assoc.delete(request)
    #     LOG.debug("Deleting %s"%self)
    #     request.dbsession.delete(self)

class VersionLink(BaseMixin, AttrMixin, ProjectScopedParentMixin, SQLModel, table=True):
    __tablename__ = "version_link_t"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "from_version_id",
            "to_version_id",
            name="version_link_name_from_to_uix",
        ),
    )
    name: str = Field(max_length=1024)
    from_version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    # from_version: Version = Relationship(
    #     back_populates="outgoing_links",
    #     link_model=Version,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["from_version_id"]
    #     }
    # )
    to_version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    # to_version: Version = Relationship(
    #     back_populates="incoming_links",
    #     link_model=Version,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["to_version_id"]
    #     }
    # )
    PROJECT_PARENT_CLS: ClassVar = Version
    PROJECT_CLS_ATTR: ClassVar = "to_version_id"


class ItemAssoc(IdMixin, ProjectScopedParentMixin, SQLModel, table=True):
    __tablename__ = "item_assoc_t"
    __table_args__ = (
        UniqueConstraint("version_id", "name", name="version_name_item_uix"),
    )
    version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    item_id: uuid.UUID = Field(foreign_key="item_t.id", nullable=False)
    name: Optional[str] = Field(max_length=64)
    uri: Optional[str] = Field(max_length=256)
    version: Version = Relationship()
    item: "Item" = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined"
        }
    )
    PROJECT_PARENT_CLS: ClassVar = Version
    PROJECT_CLS_ATTR: ClassVar = "version_id"


class Item(BaseMixin, AttrMixin, SQLModel, table=True):
    __tablename__ = "item_t"
    location_hash: Optional[bytes] = Field(
        default=None, unique=True, index=True, nullable=False
    )
    location: Optional[str] = Field(
        max_length=512,
        default=None,
        sa_column=Column('_location', String(512))
    )
    # versions: list[Version] = Relationship(
    #     link_model=ResourceAssoc,
    #     back_populates="item",
    #     sa_relationship_kwargs={
    #         "viewonly": True
    #     }
    # )
