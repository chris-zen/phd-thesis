import os

from werkzeug.wsgi import SharedDataMiddleware

from wok.server import WokFlask, WokServer
from wok.server.proxy import ReverseProxied
from wok.server.persona import PersonaLogin

from intogensm import VERSION

# Flask application ----------------------------------------------------------------------------------------------------

app = WokFlask(__name__)

# load configuration

conf_path = os.environ["CONF_PATH"]

web_conf = ["web.cfg"]
if "SM_EXTRA_CONF" in os.environ:
	names = [c.strip() for c in os.environ["SM_EXTRA_CONF"].split(",")]
	web_conf += [n if n.endswith(".cfg") else "{}.cfg".format(n) for n in names]
web_conf = [os.path.join(conf_path, n) if not os.path.isabs(n) else n for n in web_conf]
for cfg in web_conf:
	app.config.from_pyfile(cfg)

# plug middleware apps

app.wsgi_app = ReverseProxied(app.wsgi_app)

# http://werkzeug.pocoo.org/docs/middlewares/#werkzeug.wsgi.SharedDataMiddleware

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/help' : os.path.join(os.path.dirname(__file__), "help")
})

# Wok server -----------------------------------------------------------------------------------------------------------

wok_server = WokServer(app)
persona = PersonaLogin(app)

def cleanup():
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
	if eval_ctx.autoescape:
		result = Markup(result)
	return result
