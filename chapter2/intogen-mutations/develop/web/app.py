import os
import time

from werkzeug.wsgi import SharedDataMiddleware

from wok.server import WokFlask, WokServer
from wok.server.proxy import ReverseProxied
from wok.server.persona import PersonaLogin

from intogensm import VERSION

# Flask application ----------------------------------------------------------------------------------------------------

app = WokFlask(__name__)

# load app configuration

"""
The following environment variables can be defined:

* WEB_CONF_PATH specifies a base path where configuration files can be found
* WEB_CONF_FILES is a ':' separated list of configuration files. The extension can be omitted if it is .cfg.

Example:

    $ export WEB_CONF_PATH=/opt/intogen/conf
    $ export WEB_CONF_FILES=web:limits

This will load:

* /opt/intogen/conf/web.cfg
* /opt/intogen/conf/limits.cfg
"""

app.load_conf(conf_files=["web.cfg"])

# plug middleware apps

app.wsgi_app = ReverseProxied(app.wsgi_app)

# http://werkzeug.pocoo.org/docs/middlewares/#werkzeug.wsgi.SharedDataMiddleware

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/help' : os.path.join(os.path.dirname(__file__), "help")
})

# Wok server -----------------------------------------------------------------------------------------------------------

"""
The following app configuration variables or environment variables can be defined:

* WOK_CONF_PATH specifies a base path where configuration files can be found.
* WOK_CONF_FILES is a ':' separated list of configuration files. The extension can be omitted if it is .conf.
* WOK_CONF_ARGS Arguments like in the command line.

Example:

    $ export WOK_CONF_PATH=/opt/intogen/conf
    $ export WOK_CONF_FILES=system:logs

This will load:

* /opt/intogen/conf/system.conf
* /opt/intogen/conf/logs.conf
"""

wok_server = WokServer(app, conf_files=["system.conf"])

persona = PersonaLogin(app)

def startup():
	wok_server.engine.start(wait=False)
	while not wok_server.engine.running():
		time.sleep(1.0)

def cleanup():
	"""
	Called from gunicorn when the app is stopped.
	:return:
	"""
	wok_server.engine.stop()

# Jinja filters --------------------------------------------------------------------------------------------------------

from datetime import datetime
from jinja2 import evalcontextfilter, Markup

@app.template_filter()
@evalcontextfilter
def datetimefmt(eval_ctx, value, relative_datetime=None):
	if value is None:
		return ""
	if relative_datetime is None:
		relative_datetime = datetime.today()
	if value.date() == relative_datetime.date():
		result = value.strftime("%H:%M:%S")
	else:
		result = value.strftime("%c")
	if eval_ctx.autoescape:
		result = Markup(result)
	return result

@app.template_filter()
@evalcontextfilter
def elapsed_time(eval_ctx, value):
	result = str(value)
	result = result.split(".")[0]
	if eval_ctx.autoescape:
		result = Markup(result)
	return result
