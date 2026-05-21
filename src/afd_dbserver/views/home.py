from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/")
def read_root(request: Request):
    body = {
        "SERVER_VERSION": 1,
        "API_VERSION": 1,
        "DB_URL": "yay"
    }
    return {
        "data": body
    }
    # return templates.TemplateResponse(
    #     request,
    #     name="index.html",
    #     context={
    #         "request": request,
    #         "data": body,
    #         "title": "AFD-API"
    #     }
    # )
