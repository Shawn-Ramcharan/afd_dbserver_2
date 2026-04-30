from fastapi import FastAPI
from afd_dbserver.routes import (
    project,
    location,
    appliance,
    physical_asset
)

app = FastAPI()

app.include_router(project.router, prefix="/projects", tags=["projects"])
app.include_router(location.router, prefix="/locations", tags=["locations"])
app.include_router(appliance.router, prefix="/appliances", tags=["appliances"])
app.include_router(physical_asset.router, prefix="/physical_assets", tags=["physical_assets"])

# @app.get("/projects", response_model=list[Any])
# def home_page():
#     projects = [{"home": "home"}]
#     return projects

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8008)
