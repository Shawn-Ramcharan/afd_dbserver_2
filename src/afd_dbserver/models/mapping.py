import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from ..exc import NotFoundError

if TYPE_CHECKING:
    from .virtual_asset import VirtualAssetRevision

class Mapping(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """Describes a relationship between a source skeleton and a target
    skeleton, used for retargeting motion. Many-to-Many
    """

    __tablename__ = "mapping_t"
    __table_args__ = (
        UniqueConstraint(
            "name", "source_id", "target_id", name="mapping_name_source_target_uix"
        ),

    )
    name: Optional[str] = Field(default="default", max_length=128)
    fqn: Optional[str] = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    source_id: uuid.UUID = Field(
        foreign_key="virtual_asset_revision_t.id",
        nullable=False,
    )
    source: "VirtualAssetRevision" = Relationship(
        back_populates="source_mappings",
        sa_relationship_kwargs={
            "foreign_keys": "Mapping.source_id",
            "lazy": "joined"
        }
    )
    target_id: uuid.UUID = Field(
        foreign_key="virtual_asset_revision_t.id",
        nullable=False
    )
    target: "VirtualAssetRevision" = Relationship(
        back_populates="target_mappings",
        sa_relationship_kwargs={
            "foreign_keys": "Mapping.target_id",
            "lazy": "joined"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="mapping"
    )
    
    @staticmethod
    def get_fqn_string(source_: VirtualAssetRevision, target_: VirtualAssetRevision):
        return f"{source_.virtual_asset.code}_r{source_.number}_to_{target_.virtual_asset.code}_r{target_.number}"

    @classmethod
    def create(cls, payload: SQLModel, dbsession: Session):
        # determine the fully-qualified-name (fqn)
        try:
            source_ = VirtualAssetRevision.get_by_id(payload.source_id, dbsession)
            target_ = VirtualAssetRevision.get_by_id(payload.target_id, dbsession)
        except NoResultFound as err:
            raise NotFoundError(err)
        payload.fqn = cls.get_fqn_string(source_, target_)
        model = super(Mapping, cls).create(payload, dbsession)
        return model

    @classmethod
    def get_all(cls, dbsession: DbSession, project_id: uuid.UUID):
        return cls.get_all_by_project(dbsession, project_id)
        # return request.dbsession.query(cls).join(Project).filter(Project.id==project_id).order_by(desc(cls.creation_date)).all()

    # TODO: continue with updating functions

    @classmethod
    def get(cls, request, params):
        query = request.dbsession.query(Mapping).filter(and_(Mapping.source_id==params["source_id"], Mapping.target_id==params["target_id"],Mapping.name==params["name"]))
        try:
            return query.one()
        
        except NoResultFound:
            raise HTTPNotFound("No Mapping matching parameters source_id={0}, target_id={1}, name={2} found.".format(params["source_id"], params["target_id"], params["name"]))

    def update(self, request, params):
        if 'source_id' in params or 'target_id' in params:
            if 'source_id' in params:
                try:
                    self.source = VirtualAssetRevision.get_by_id(request, params["source_id"])
                except NoResultFound as err:
                    raise HTTPNotFound(err)
                LOG.debug("Source: %s"%self.source)
            if 'target_id' in params:
                try:
                    self.target = VirtualAssetRevision.get_by_id(request, params["target_id"])
                except NoResultFound as err:
                    raise HTTPNotFound(err)
                LOG.debug("Target: %s"%self.target)
            fqn = "%s_r%d_to_%s_r%d"%(self.source.virtual_asset.code, self.source.number, self.target.virtual_asset.code, self.target.number)
            params["fqn"] = fqn
        # update attributes
        for key in params:
            if not hasattr(self, key):
                continue
            if key=="attrs":
                self.merge_attrs(params[key])
            else:
                setattr(self, key, params[key])
        self.update_stamp(request)
        request.dbsession.flush()



