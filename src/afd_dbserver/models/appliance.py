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

class EApplianceType(enum.Enum):
    giant           = "giant"
    motive          = "motive"
    ajaKiPro        = "ajaKiPro"
    ajaKona         = "ajaKona"
    unrealEngine    = "unrealEngine"
    mugshot         = "mugshot"
    bmdhyperdeck    = "bmdhyperdeck"
    motionbuilder   = "motionbuilder"
    livelinkface    = "livelinkface"

class Appliance(BaseMixin, AttrMixin, SQLModel, table=True):
    """ A physical device on the mocap stage, e.g. witness camera, HMD, AJA KiPro etc.  
    """
    __tablename__ = "appliance_t"
    __table_args__ = (UniqueConstraint(
        'code',
        'type_',
        name='appliance_code_type_uix'
    ),)
    code: str = Field(max_length=32, unique=True, nullable=False)
    type_: EApplianceType = Field(
        sa_column=Column(SqlaEnum(EApplianceType,name='eappliancetype'), nullable=False)
    )
    name: Optional[str] = Field(default="", max_length=128)
    serial_number: Optional[str] = Field(default="", index=True)
    is_active: Optional[bool] = Field(default=True)

    @classmethod
    def get_all(
        cls,
        dbsession: Session,
        type_: Optional[EApplianceType] = None,
        include_inactive: bool = False
    ):
        if include_inactive is True:
            appliances = select(cls)
        else:
            appliances = select(cls).where(cls.is_active.is_(True))
        if type_ is not None:
            appliances = appliances.where(cls.type_ == type_)
        return dbsession.exec(appliances).all()

    @classmethod
    def get_by_code(cls, dbsession: Session, code: str):
        try:
            return dbsession.exec(select(cls).where(cls.code == code)).one()
        except NoResultFound:
            return None
