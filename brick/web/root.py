import os
from fastapi import Request
from starlette.responses import RedirectResponse
from brick.exceptions import ValidationError


async def home(request: Request):
    return request.app.templates.TemplateResponse('home.html', dict(request=request))


async def config(request: Request):
    success_url = '/config'
    config_manager = request.app.config_manager

    errors = dict()
    if request.method == 'POST':
        data = await request.form()
        config_text = data['config']
        try:
            config_manager.validate(config_text)
            await config_manager.save(config_text)
            return RedirectResponse(success_url, status_code=302)
        except ValidationError as error:
            errors = error.message_dict
        except Exception as err:
            errors = dict(config=[str(err)])
    else:
        config_text = await config_manager.get_config_text()

    context = dict(request=request, errors=errors, config_text=config_text)
    return request.app.templates.TemplateResponse('config.html', context)
