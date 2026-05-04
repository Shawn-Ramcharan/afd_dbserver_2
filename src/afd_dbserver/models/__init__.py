from sqlmodel import (
    SQLModel,
    create_engine
)
from sqlmodel import Session as DbSession
from .project import Project
from .location import Location
from .appliance import Appliance
from .physical_asset import PhysicalAsset
from .device import Device
from .virtual_asset import VirtualAsset, VirtualAssetRevision
from .solver_setup import SolverSetup
from .mapping import Mapping
from .session import Session
from .volume import Volume
from .take import Take
from .capture_load import CaptureLoad, CaptureLoadEntry, CaptureLoadEntryVersion
from .timecode_range import TimecodeRange
from .note import Note, NoteAssoc
from .take_select import TakeSelect
from .take_select_list import TakeSelectList, TakeSelectListAssoc
from .resource import ResourceAssoc, Resource, Version, VersionLink, Item, ItemAssoc


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
