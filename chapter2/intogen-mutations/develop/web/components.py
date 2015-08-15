import os

from flask import (Blueprint, current_app, request, session, redirect, url_for,
				   render_template, abort, flash, jsonify, send_file, g, get_template_attribute)

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.core.runstates import STATES, FINISHED, FAILED, ABORTED, ABORTING, RUNNING, PAUSED, WAITING

bp = Blueprint("components", __name__)

@bp.route("/<case_id>")
@login_required
def index(case_id):
	components = [] #TODO
	return render_template("components.html", components=components)

@bp.route("/__list/<case_id>")
def list(case_id):
	if current_user.is_anonymous():
		return redirect(url_for("components.index", case_id=case_id)) # FIXME Shouldn't be an abort() ?

	components = [] # TODO

	render = get_template_attribute("components.jinja2", "render")
	return render_list(g, current_user, components)