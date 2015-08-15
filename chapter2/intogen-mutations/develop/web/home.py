import os
import uuid
import shutil

from flask import (render_template, request, redirect, session, make_response,
					abort, url_for, current_app, g, Response, flash, send_file)

from flask.ext.login import (current_user, login_required, login_user, logout_user,
							confirm_login, fresh_login_required)

from intogensm import VERSION
from intogensm.onexus import Onexus

from app import app, wok_server

# Blueprints -----------------------------------------------------------------------------------------------------------

import analysis
import cases
import components
import examples

app.register_blueprint(analysis.bp, url_prefix="/analysis")
app.register_blueprint(cases.bp, url_prefix="/cases")
app.register_blueprint(components.bp, url_prefix="/components")
app.register_blueprint(examples.bp, url_prefix="/examples")
#app.register_blueprint(admin, url_prefix="/admin")

# ----------------------------------------------------------------------------------------------------------------------

@app.before_request
def before_request():
	if not "session_id" in session:
		session["session_id"] = str(uuid.uuid4())
	g.session_id = session["session_id"]

	g.demo = current_app.config.get("DEMO_MODE", False)

	g.version = VERSION

@app.teardown_request
def teardown_request(exception):
	pass

# Views ----------------------------------------------------------------------------------------------------------------

@app.route('/')
def index():
	return render_template("index.html", hidden_header=True)

@app.route('/help')
def help():
	path = request.args.get("path")
	return render_template("help.html", hidden_header=True, path=path)

@app.route('/download')
def download():
	return render_template("download.html", hidden_header=True)

@app.route("/signin", methods=["GET"])
def signin():
	return render_template("signin.html", next=request.args.get("next"))

if __name__ == "__main__":
	wok_server.run(version=VERSION)