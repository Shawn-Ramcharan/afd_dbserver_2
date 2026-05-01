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


# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: http://alembic.zzzcomputing.com/en/latest/naming.html
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

DATE_STR = "%Y-%m-%d"

metadata = SQLModel.metadata
metadata.naming_convention = NAMING_CONVENTION
metadata.create_all(engine)

def get_session():
    with DbSession(engine) as dbsession:
        yield dbsession
