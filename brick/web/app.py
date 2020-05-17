import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates'))


class App(FastAPI):
    pass


app = App()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse('home.html', dict(request=request))
