from fastapi import FastAPI
from afd_dbserver.routes import (
    project,
    location,
    appliance
)

app = FastAPI()

app.include_router(project.router, tags=["projects"])
app.include_router(location.router, tags=["locations"])
app.include_router(appliance.router, tags=["appliance"])

# @app.get("/projects", response_model=list[Any])
# def home_page():
#     projects = [{"home": "home"}]
#     return projects

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8008)
