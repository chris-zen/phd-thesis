import os
import shutil

from flask import (Blueprint, current_app, request, session, redirect, url_for,
				   render_template, abort, flash, jsonify, send_file, g, get_template_attribute)

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.core.runstates import STATES, FINISHED, FAILED, ABORTED, ABORTING, RUNNING, PAUSED, WAITING

from intogensm.onexus import Onexus
from intogensm.constants.oncodrivefm import *
from intogensm.constants.oncodriveclust import *
from intogensm.projects.results import ProjectResults
from intogensm.config.paths import get_results_path
from intogensm.analysis import PROJECT_NAME, MUTATIONS_FLOW_NAME, DEFAULT_PLATFORM_NAME, download_files

from app import wok_server

from constants import *
from utils import get_project_conf

bp = Blueprint("cases", __name__)


# ----------------------------------------------------------------------------------------------------------------------

def __task_count_by_state(case):
	if case is None:
		counts = {}
	else:
		counts = case.task_count_by_state

	total = 0
	for state in STATES:
		if state not in counts:
			counts[state] = 0
		else:
			total += counts[state]

	return counts, total

def __engine_case_progress(case):
	counts, total = __task_count_by_state(case)
	progress = []

	total_percent = 0
	for state in [FINISHED, FAILED, ABORTED, ABORTING, RUNNING, PAUSED, WAITING]:
		count = counts[state]
		if total == 0:
			percent = 0
		else:
			percent = round(100.0 * count / total)
		total_percent += percent
		progress += [{
			"state" : state.title,
			"count" : count,
			"tooltip" : "{0}: {1}".format(state.title, count),
			"percent" : percent }]

	return progress

	"""
	info_tooltip = []
	info_count = 0
	for state in [READY, PAUSED, WAITING]:
		count = counts[state.title]
		info_tooltip += ["{0}: {1}".format(state.title, count)]
		info_count += count

	progress["info"] = {
		"count" : info_count,
		"tooltip" : ", ".join(info_tooltip),
		"percent" : 100 - total_percent }
	"""

def __engine_case_exceptions(case):
	exceptions = []
	for task in case.tasks:
		if task.state == FAILED:
			wi_exceptions = []
			for wi in case.workitems(task.cname):
				if wi.state == FAILED:
					wi_exceptions += [dict(
						index="{:08d}".format(wi.index),
						exitcode=wi.result.get("exitcode"),
						exception=wi.result.get("exception", "Internal error"),
						trace=wi.result.get("trace"))]
			prefix = "{}.".format(MUTATIONS_FLOW_NAME)
			exceptions += [dict(
				cname=task.cname[len(prefix):] if task.cname.startswith(prefix) else task.cname,
				workitems=wi_exceptions)]
	return exceptions

def __load_case_info(case, except_enabled=False, quality_enabled=False):
	wok = current_app.wok
	case_info = dict(
		id=case.id,
		name=case.name,
		state=case.state.title if case.state is not None else None,created=case.created,
		started=case.started,
		finished=case.finished,
		removed=case.removed)

	if case.state is not None:
		case_info["state"] = case.state.title

	if case.properties is not None:
		conf = get_project_conf()
		results_path = get_results_path(conf)
		project_path = os.path.join(results_path, case.properties["path"])

		quality = None
		if quality_enabled:
			project_results = ProjectResults(path=project_path)
			quality = project_results.load_quality_control()

		zip_path = os.path.join(project_path, "results.zip")
		website_path = os.path.join(project_path, "website", "results", "project.tsv")
		case_info.update(
			analysis_type=case.properties["analysis_type"],
			results_available=os.path.exists(zip_path),
			website_available=os.path.exists(website_path),
			quality=quality if quality is not None and len(quality) > 0 else None)

	engine_case = wok.engine.case(case.engine_name)
	if engine_case is not None:
		exceptions = None
		if except_enabled:
			exceptions = __engine_case_exceptions(engine_case)

		case_info.update(
			state=engine_case.state.title,
			started=engine_case.started,
			finished=engine_case.finished,
			elapsed=engine_case.elapsed,
			progress=__engine_case_progress(engine_case),
			exceptions=exceptions)

	return case_info

def __load_cases_info(page=1, cases_per_page=10):
	wok = current_app.wok
	cases = wok.cases(current_user) #TODO pagination
	cases_info = []
	for case in cases:
		if True or not case.removed: #FIXME trick to avoid the engine bug with forever aborting cases
			cases_info += [__load_case_info(case)]
	return cases_info

_PREDEFINED_PARAMS = [
	([COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS], ASSEMBLY_KEY, "hg19", "Genome assembly", lambda value: ASSEMBLY_LABEL[value]),
	([COHORT_ANALYSIS], ONCODRIVEFM_GENES_THRESHOLD_KEY, ONCODRIVEFM_GENES_THRESHOLD, "OncodriveFM genes threshold", None),
	([COHORT_ANALYSIS], ONCODRIVEFM_PATHWAYS_THRESHOLD_KEY, ONCODRIVEFM_PATHWAYS_THRESHOLD, "OncodriveFM pathways threshold", None),
	([COHORT_ANALYSIS], ONCODRIVECLUST_GENES_THRESHOLD_KEY, ONCODRIVECLUST_MUTATIONS_THRESHOLD, "OncodriveCLUST genes threshold", None),
	([COHORT_ANALYSIS], ONCODRIVECLUST_FILTER_ENABLED_KEY, True, "OncodriveFM and OncodriveCLUST genes filter", lambda value: "Enabled" if value == True else "Disabled")
]

# Wok signals ----------------------------------------------------------------------------------------------------------

@wok_server.case_finished.connect
def case_finished(case, **kwargs):
	conf = wok_server.engine.projects.project_conf(PROJECT_NAME, platform_name=DEFAULT_PLATFORM_NAME)
	conf["user_id"] = case.owner.nick
	conf["workspace"] = DEFAULT_WORKSPACE
	results_path = get_results_path(conf)
	engine_case = wok_server.engine.case(case.engine_name)
	if engine_case is not None:
		download_files(wok_server.logger, engine_case.name, engine_case.storages, "results/", results_path)

@wok_server.case_removed.connect
def case_removed(case, **kwargs):
	conf = wok_server.engine.projects.project_conf(PROJECT_NAME, platform_name=DEFAULT_PLATFORM_NAME)
	conf["user_id"] = case.owner.nick
	conf["workspace"] = DEFAULT_WORKSPACE
	results_path = get_results_path(conf)
	project_path = os.path.join(results_path, case.properties["path"])

	user = case.owner
	onexus_projects = conf.get("website.projects_list")
	if onexus_projects is not None and os.path.exists(os.path.join(project_path, "website")):
		wok_server.logger.info("[{}] Removing Onexus project {} ...".format(user.nick, case.name))
		onexus = Onexus(onexus_projects)
		onexus.remove_project(user.nick, case.name)

	wok_server.logger.info("[{}] Removing case files {} ...".format(user.nick, case.name))
	if os.path.exists(project_path):
		shutil.rmtree(project_path)

# ----------------------------------------------------------------------------------------------------------------------

@bp.route("/")
@login_required
def index():
	try:
		highlight = int(request.args.get("highlight"))
	except:
		highlight = None

	cases_info = __load_cases_info() #TODO pagination

	return render_template("cases.html", cases=cases_info, browser_enabled=g.demo, highlight=highlight)

@bp.route("/__list")
def ajax_list():
	if current_user.is_anonymous():
		abort(401)

	try:
		highlight = int(request.args.get("highlight"))
	except:
		highlight = None

	cases_info = __load_cases_info() #TODO pagination

	browser_enabled = g.demo

	cases_list_macro = get_template_attribute("cases.jinja2", "cases_list")
	return cases_list_macro(current_user, cases_info, True, browser_enabled, highlight)

@bp.route("/<int:case_id>")
@login_required
def details(case_id):
	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		flash("Case does not exist, there is nothing to show", "error")
		return redirect(url_for(".index"))

	case_info = __load_case_info(case, except_enabled=True, quality_enabled=True)

	conf = case.conf
	case_info["params"] = params = []
	atype = case.properties["analysis_type"]
	for atypes, key, default, title, value_fn in _PREDEFINED_PARAMS:
		if atype in atypes and (key in conf or default is not None):
			value = conf.get(key, default)
			params += [dict(title=title, value=value_fn(value) if value_fn is not None else value)]

	case_info["genes_filter_enabled"] = conf.get(ONCODRIVEFM_FILTER_ENABLED_KEY, False)

	return render_template("case.html", current_user=current_user, case=case_info, browser_enabled=g.demo)

@bp.route("/<int:case_id>/__header")
def ajax_header(case_id):
	if current_user.is_anonymous():
		abort(401)

	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		abort(404)

	case_info = __load_case_info(case)

	browser_enabled = g.demo

	cases_list_macro = get_template_attribute("cases.jinja2", "cases_list")
	return cases_list_macro(current_user, [case_info], False, browser_enabled)

@bp.route("/<int:case_id>/__details")
def ajax_details(case_id):
	if current_user.is_anonymous():
		abort(401)

	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		abort(404)

	case_info = __load_case_info(case, except_enabled=True, quality_enabled=True)

	case_details_macro = get_template_attribute("cases.jinja2", "case_details")
	return case_details_macro(case_info)

@bp.route("/<int:case_id>/__errors")
def ajax_errors(case_id):
	if current_user.is_anonymous():
		abort(401)

	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		abort(404)

	case_info = __load_case_info(case, except_enabled=True)

	errors_macro = get_template_attribute("cases.jinja2", "errors")
	return errors_macro(case_info)

@bp.route("/<int:case_id>/__quality")
def ajax_quality(case_id):
	if current_user.is_anonymous():
		abort(401)

	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		abort(404)

	case_info = __load_case_info(case, quality_enabled=True)

	quality_control_macro = get_template_attribute("cases.jinja2", "quality_control_panel")
	return quality_control_macro(case_info)

@bp.route("/<int:case_id>/__quality_data")
def json_quality(case_id):
	if current_user.is_anonymous():
		abort(401)

	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		abort(404)

	case_info = __load_case_info(case, quality_enabled=True)
	quality = case_info["quality"]

	return jsonify(quality if quality is not None else {})

@bp.route("/download/<int:case_id>")
@login_required
def download(case_id):
	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		flash("Case does not exist, there is nothing to download", "error")
		return redirect(url_for(".index"))

	current_app.logger.info("[{}] Downloading case results {} ({})...".format(current_user.nick, case.name, case.engine_name))

	conf = get_project_conf()
	results_path = get_results_path(conf)
	project_path = os.path.join(results_path, case.properties["path"])
	dest_path = os.path.join(project_path, "results.zip")
	if not os.path.exists(dest_path):
		flash("Sorry, there were an internal error and the results are not available", "error")
		app.logger.error("[{}] results.zip not available for case {} at {}".format(current_user.nick, case.id, project_path))
		return redirect(url_for(".index"))

	return send_file(
				dest_path,
				mimetype="application/x-gzip",
				as_attachment=True,
				attachment_filename="IntOGen-Mutations-{}.zip".format(case.name))

@bp.route("/remove/<int:case_id>", methods=["GET", "POST"])
@login_required
def remove(case_id):
	case = current_app.wok.case_by_id(case_id, current_user)
	if case is None:
		if request.method == "GET":
			flash("Case does not exist, it can not be removed", "error")
		else:
			return jsonify(dict(status="error", msg="Case does not exist, it can not be removed"))
	else:
		if not case.removed:
			current_app.logger.info("[{}] Removing case {} ...".format(current_user.nick, case.name))
			current_app.wok.remove_case(current_user, case)

	if request.method == "GET":
		return redirect(url_for(".index"))
	else:
		return jsonify(dict(status="ok", case_name=case.name))
