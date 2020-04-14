import gc
import ure as re
import uasyncio as asyncio
from picoweb import WebApp, start_response
from brick import config
from brick.logging import LEVEL_NAME


class Server(WebApp):
    def __init__(self, log_collector, **kwargs):
        routes = [
            (re.compile("^/$"), self.index),
            (re.compile("^/config[/]?$"), self.config),
            (re.compile("^/log/lines/(info|debug|warning)[/]?$"), self.log_lines),
            (re.compile("^/log/(info|debug|warning)[/]?$"), self.log),
            (re.compile("^/log[/]?$"), self.log_redirect),
        ]
        kwargs['routes'] = routes
        super().__init__(None, **kwargs)
        self.log_collector = log_collector
        self.log = self.log_collector.get_logger('web')

    def start(self, logger=None, debug=False):
        host = '0.0.0.0'
        port = 80
        gc.collect()
        self.debug = int(debug)
        self.init()
        for app in self.mounts:
            app.init()
        loop = asyncio.get_event_loop()
        task = loop.create_task(asyncio.start_server(self._handle, host, port))
        self.log.info('Server started on port {}'.format(port))
        return task

    def redirect(self, response, location):
        yield from start_response(response, status=302, headers=dict(Location=location))

    def index(self, request, response):
        yield from start_response(response)
        yield from self.render_template(response, 'index.html', ())

    def config(self, request, response):
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

    def log_redirect(self, request, response):
        yield from self.redirect(response, '/log/info/')

    def log(self, request, response):
        level = request.url_match.group(1)
        yield from start_response(response)
        yield from self.render_template(response, 'log.html', (level,))

    def log_lines(self, request, response):
        level = request.url_match.group(1)
        headers = {'Cache-Control': 'no-cache'}
        yield from start_response(response, content_type='text/event-stream', headers=headers)
        collector = LogLineCollector()
        try:
            consumer_id = self.log_collector.add_consumer(collector.callback, level=level, components=dict())
            yield from collector.stream(response)
        except OSError:
            self.log.info('Client closed connection.')
            pass
        except Exception as error:
            self.log.exception('log_lines error', error)
        finally:
            self.log_collector.remove_consumer(consumer_id)


class LogLineCollector():
    def __init__(self):
        self.line = None
        self.event = asyncio.Event()

    def stream(self, response):
        while True:
            await self.event.wait()
            if self.line:
                yield from response.awrite('data: {level} {component} {message}\n\n'.format(**self.line))
                self.line = None
            self.event.clear()

    async def callback(self, level, component, message, *args, **kwargs):
        self.line = dict(level=LEVEL_NAME[level], component=component, message=message)
        self.event.set()
