import gc
import logging
import uasyncio as asyncio
from picoweb import WebApp, start_response
from brick import config


class Server(WebApp):
    def __init__(self, **kwargs):
        routes = [
            ('/', self.index)
        ]
        kwargs['routes'] = routes
        super().__init__(None, **kwargs)

    def start(self, logger=None, debug=False):
        self.log = logger or logging.getLogger('web')
        host = '0.0.0.0'
        port = 80
        gc.collect()
        self.debug = int(debug)
        self.init()
        for app in self.mounts:
            app.init()
        loop = asyncio.get_event_loop()
        task = loop.create_task(asyncio.start_server(self._handle, host, port))
        self.log.info(' Server started on port {}'.format(port))
        return task

    def redirect(self, response, location):
        yield from start_response(response, status=302, headers=dict(Location=location))

    def index(self, request, response):
        gc.collect()
        success_url = '/'
        method = request.method

        error = None
        if method == 'POST':
            await request.read_form_data()
            config_text = request.form['config']
            try:
                config.validate_config(config_text)
                config.save_config(config_text)
                yield from self.redirect(response, success_url)
                return
            except Exception as err:
                error = str(err)
        else:
            config_text = config.get_config_text()

        error_text = ''
        if error:
            error_text = '<h2>Configuration error: {}</h2>'.format(error)

        content = """\
        <!DOCTYPE html>
        <html lang=en>
            <head>
                <meta charset="UTF-8" />
                <title>Brick</title>
            </head>
            <body>
                <h1>Brick Configuration</h1>
                {}
                <form action="." method="post" accept-charset="ISO-8859-1">
                    <div>
                        <textarea name="config" rows="30" cols="80">{}</textarea>
                    </div>
                    <div>
                        <input type="submit" value="Save">
                    </div>
                </form>
            </body>
        </html>
        """.format(error_text, config_text)

        yield from start_response(response)
        yield from response.awrite(content)
        return
