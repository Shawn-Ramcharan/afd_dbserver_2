from fastapi import FastAPI
from afd_dbserver.routes import (
    project,
    location,
    appliance,
    physical_asset,
    session,
    take,
    virtual_asset,
    virtual_asset_revision,
    note,
    mapping,
    solver_setup,
    device,
    volume,
    timecode_range,
    capture_load,
    capture_load_entry,
    take_select,
    take_select_list,
    # resource,
    # version,
    # item,
)

app = FastAPI()

# Global API Routes
app.include_router(project.router)
app.include_router(location.router)
app.include_router(appliance.router)
app.include_router(physical_asset.router)

# Project Scoped API Routes
app.include_router(session.project_router)
app.include_router(session.router)
app.include_router(take.project_router)
app.include_router(take.router)
app.include_router(virtual_asset.project_router)
app.include_router(virtual_asset.router)
app.include_router(virtual_asset_revision.router)
app.include_router(virtual_asset_revision.virtual_asset_router)
app.include_router(note.router)
app.include_router(mapping.project_router)
app.include_router(mapping.router)
app.include_router(solver_setup.physical_asset_router)
app.include_router(solver_setup.project_router)
app.include_router(solver_setup.router)
app.include_router(device.volume_router)
app.include_router(device.router)
app.include_router(volume.session_router)
app.include_router(volume.router)
app.include_router(capture_load.project_router)
app.include_router(capture_load.router)
app.include_router(capture_load_entry.capture_load_router)
app.include_router(capture_load_entry.versions_router)
app.include_router(capture_load_entry.capture_load_entry_version_router)
app.include_router(capture_load_entry.router)
app.include_router(timecode_range.router)
app.include_router(take_select.take_router)
app.include_router(take_select.router)
app.include_router(take_select_list.project_router)
app.include_router(take_select_list.router)

# Attr Router
# NOTE: Wiil need to add them last because
# they may affect other routers
app.include_router(project.attr_router)
app.include_router(location.attr_router)
app.include_router(appliance.attr_router)
app.include_router(physical_asset.attr_router)
app.include_router(session.attr_router)
app.include_router(take.attr_router)
app.include_router(virtual_asset.attr_router)
app.include_router(virtual_asset_revision.attr_router)
app.include_router(note.attr_router)
app.include_router(mapping.attr_router)
app.include_router(solver_setup.attr_router)
app.include_router(device.attr_router)
app.include_router(volume.attr_router)
app.include_router(capture_load.attr_router)
app.include_router(capture_load_entry.attr_router)
app.include_router(timecode_range.attr_router)
app.include_router(take_select.attr_router)
app.include_router(take_select_list.attr_router)

# @app.get("/projects", response_model=list[Any])
# def home_page():
#     projects = [{"home": "home"}]
#     return projects

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8008)
