from sqlmodel import (
    SQLModel,
    create_engine
)
from sqlmodel import Session as DbSession
from .project import Project
from .location import Location
from .appliance import Appliance
from .physical_asset import PhysicalAsset
from .session import Session

engine = create_engine("sqlite:///./afd_local.db", echo=True)
SQLModel.metadata.create_all(engine)

def get_session():
    with DbSession(engine) as dbsession:
        yield dbsession
