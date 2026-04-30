import enum
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Enum as SqlaEnum
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import (
    SQLModel,
    Session,
    Column,
    Field,
    select
)
from .mixin import BaseMixin, AttrMixin
from .project import Project

class EPhysicalAssetType(enum.IntEnum):
    performer   = 1
    prop        = 2
    camera      = 3

class PhysicalAsset(BaseMixin, AttrMixin, SQLModel, table=True):
    """ 
    """
    __tablename__ = "physical_asset_t"
    code: str = Field(max_length=32, unique=True, nullable=False)
    name: str = Field(max_length=128)
    type_: EPhysicalAssetType = Field(
        sa_column=Column(SqlaEnum(EPhysicalAssetType,name='ephysicalassettype'))
    )
    subject_id: str = Field(max_length=128, unique=True)
    # solver_setups = relationship("SolverSetup", back_populates="physical_asset")

    @classmethod
    def get_all(
        cls,
        dbsession: Session,
        type_: Optional[EPhysicalAssetType] = None,
        project: Optional[Project] = None
    ):
        physical_assets = select(cls)
        if project is not None:
            # TODO: implement when SolverSetups is implemented
            # physical_assets = physical_assets.join(SolverSetup).filter(SolverSetup.project_id==project.id)
            return []
        if type_ is not None:
            physical_assets = physical_assets.where(cls.type_ == type_)
        return dbsession.exec(physical_assets).all()

    @classmethod
    def get_by_code(cls, dbsession: Session, code: str):
        try:
            return dbsession.exec(select(cls).where(cls.code == code)).one()
        except NoResultFound:
            return None
