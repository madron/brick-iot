import os
from fastapi import Request
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates'))


async def home(request: Request):
    return templates.TemplateResponse('home.html', dict(request=request))


async def config(request: Request):
    success_url = '/config/'
    method = 'GET'

    config_manager = request.app.config_manager

    errors = dict()
    if method == 'POST':
        await request.read_form_data()
        config_text = request.form['config']
        try:
            config.validate_config(config_text)
            config.save_config(config_text)
            # yield from self.redirect(response, success_url)
            return
        except ValidationError as error:
            errors = error.message_dict
        except Exception as err:
            errors = dict(config=[str(err)])
    else:
        config_text = await config_manager.get_config_text()

    context = dict(request=request, errors=errors, config_text=config_text)
    return templates.TemplateResponse('config.html', context)


routes = [
    APIRoute('/', home),
    APIRoute('/config', config, methods=['GET']),
]
