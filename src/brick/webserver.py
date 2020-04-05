from microWebSrv import MicroWebSrv
from brick import config


class WebServer(MicroWebSrv):
    @MicroWebSrv.route('/', 'GET')
    @MicroWebSrv.route('/', 'POST')
    def config_view(httpClient, httpResponse, routeArgs=None):
        success_url = '/'
        method = httpClient.GetRequestMethod()

        error = None
        if method == 'POST':
            config_text = httpClient.ReadRequestPostedFormData()['config']
            try:
                config.validate_config(config_text)
                config.save_config(config_text)
                httpResponse.WriteResponseRedirect(success_url)
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
                        <textarea name="config" rows="40" cols="100">{}</textarea>
                    </div>
                    <div>
                        <input type="submit" value="Save">
                    </div>
                </form>
            </body>
        </html>
        """.format(error_text, config_text)

        httpResponse.WriteResponseOk(
            headers=None,
            contentType="text/html",
            contentCharset="UTF-8",
            content=content,
        )
        return
