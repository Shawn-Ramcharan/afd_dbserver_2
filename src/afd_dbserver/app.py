from fastapi import FastAPI
from afd_dbserver.routes import (
    project,
    location,
    appliance,
    physical_asset,
    session
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

# Attr Router
# NOTE: Wiil need to add them last because
# they may affect other routers
app.include_router(project.attr_router)
app.include_router(location.attr_router)
app.include_router(appliance.attr_router)
app.include_router(physical_asset.attr_router)
app.include_router(session.attr_router)

# @app.get("/projects", response_model=list[Any])
# def home_page():
#     projects = [{"home": "home"}]
#     return projects

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8008)
