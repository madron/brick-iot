import gc
import logging
import uasyncio as asyncio
from picoweb import WebApp, start_response
from brick import config


class Server(WebApp):
    def __init__(self, **kwargs):
        routes = [
            ('/', self.index),
            ('/log', self.log),
            ('/log/lines', self.log_lines),
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

        error = ''
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

        yield from start_response(response)
        yield from self.render_template(response, 'config.html', (error, config_text))
        return

    def log(self, request, response):
        yield from start_response(response)
        yield from self.render_template(response, 'log.html', ())

    def log_lines(self, request, response):
        headers = {'Cache-Control': 'no-cache'}
        yield from start_response(response, content_type='text/event-stream', headers=headers)
        counter = 0
        while True:
            counter += 1
            yield from response.awrite('data: {}\n\n'.format(counter))
            await asyncio.sleep(1)
