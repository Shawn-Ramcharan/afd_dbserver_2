class ResourceAssoc(Base, IdMixin):
    __tablename__ = "resource_assoc_t"
    resource_id = Column(ForeignKey("resource_t.id"), unique=True)
    resource = relationship("Resource")
    project_id =  Column(ForeignKey("project_t.id"))
    project = relationship("Project")
    solver_setup_id = Column(ForeignKey("solver_setup_t.id"))
    solver_setup = relationship("SolverSetup")
    virtual_asset_revision_id = Column(ForeignKey("virtual_asset_revision_t.id"))
    virtual_asset_revision = relationship("VirtualAssetRevision")
    mapping_id = Column(ForeignKey("mapping_t.id"))
    mapping = relationship("Mapping")
    session_id = Column(ForeignKey("session_t.id"))
    session = relationship("Session")
    volume_id = Column(ForeignKey("volume_t.id"))
    volume = relationship("Volume")
    device_id = Column(ForeignKey("device_t.id"))
    device = relationship("Device")
    take_id = Column(ForeignKey("take_t.id"))
    take = relationship("Take")
    take_select_id = Column(ForeignKey("take_select_t.id"))
    take_select = relationship("TakeSelect")

class Resource(Base, BaseMixin, AttrMixin, ProjectScopedDataMixin, ProjectScopedAssocMixin):
    __tablename__ = "resource_t"
    name = Column(String(64))
    group = Column(String(64))
    uri = Column(String(256))
    project_id = Column(ForeignKey("project_t.id"), nullable=False)
    project = relationship("Project")
    PROJECT_ASSOC_CLS = ResourceAssoc


class Version(Base, BaseMixin, AttrMixin, ProjectScopedDataMixin):

    LATEST = 'latest'
    OFFICIAL = 'official'

    __tablename__ = "version_t"
    number = Column(Integer)
    tags = Column(ARRAY(Text))
    description = Column(String(1024))
    is_committed = Column(Boolean, default=False)
    uri = Column(String(256))
    resource_id = Column(ForeignKey('resource_t.id'), nullable=False)
    resource = relationship(Resource, backref="versions")
    project_id = Column(ForeignKey("project_t.id"), nullable=False)
    project = relationship("Project")
    outgoing_links = relationship("VersionLink", back_populates="from_version", foreign_keys="VersionLink.from_version_id")
    incoming_links = relationship("VersionLink", back_populates="to_version", foreign_keys="VersionLink.to_version_id")

class VersionLink(Base, BaseMixin, AttrMixin, ProjectScopedParentMixin):
    __tablename__ = "version_link_t"
    __table_args__ = ( UniqueConstraint('name', 'from_version_id', 'to_version_id', name='version_link_name_from_to_uix'), )
    name = Column(String(1024))
    from_version_id = Column(ForeignKey("version_t.id"), nullable=False)
    from_version = relationship(Version, back_populates="outgoing_links", foreign_keys=from_version_id)
    to_version_id = Column(ForeignKey("version_t.id"), nullable=False)
    to_version = relationship(Version, back_populates="incoming_links", foreign_keys=to_version_id)
    PROJECT_PARENT_CLS = Version
    PROJECT_CLS_ATTR = "to_version_id"


class ItemAssoc(Base, IdMixin, ProjectScopedParentMixin):
    __tablename__ = "item_assoc_t"
    __table_args__ = ( UniqueConstraint('version_id', 'name', name='version_name_item_uix'), )
    version_id = Column(ForeignKey("version_t.id"), nullable=False)
    item_id = Column(ForeignKey("item_t.id"), nullable=False)
    name = Column(String(64))
    uri = Column(String(256))
    version = relationship("Version")
    item = relationship("Item", lazy="joined")
    PROJECT_PARENT_CLS = Version
    PROJECT_CLS_ATTR = "version_id"

class Item(Base, BaseMixin, AttrMixin):
    __tablename__ = "item_t"
    location_hash = Column(LargeBinary(16), unique=True, index=True, nullable=False)
    _location = Column(String(512))
