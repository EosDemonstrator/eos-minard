from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

app.config.from_envvar('MINARD_SETTINGS', silent=False)

# https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
@app.before_request
def setup_logging():
    app.before_request_funcs[None].remove(setup_logging)
    if not app.debug:
        import logging
        gunicorn_logger = logging.getLogger('gunicorn.error')
        for handler in gunicorn_logger.handlers:
            app.logger.addHandler(handler)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

import minard.views

