import os
import re

from flask import Blueprint, g, current_app, request, session, redirect, url_for, render_template, abort, flash

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.config import ConfigBuilder

from intogensm.utils import normalize_id
from intogensm.projects.defaults import DEFAULT_ASSEMBLY
from intogensm.constants.oncodrivefm import ONCODRIVEFM_GENES_THRESHOLD, ONCODRIVEFM_PATHWAYS_THRESHOLD
from intogensm.constants.oncodriveclust import ONCODRIVECLUST_MUTATIONS_THRESHOLD
from intogensm.analysis import (
	PROJECT_NAME, MUTATIONS_FLOW_NAME, DEFAULT_PLATFORM_NAME,
	init_project_files, upload_files)

from constants import *
from utils import unique_project_id, get_paths

bp = Blueprint("analysis", __name__)

@bp.route("/<type>", methods=["GET", "POST"])
@login_required
def run(type):
	if type not in [COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS]:
		abort(400)

	if request.method == "GET":
		form = dict(
			ofm_genes_threshold=ONCODRIVEFM_GENES_THRESHOLD,
			ofm_pathways_threshold=ONCODRIVEFM_PATHWAYS_THRESHOLD,
			oclust_genes_threshold=ONCODRIVECLUST_MUTATIONS_THRESHOLD)

		return render_template("analysis.html", type=type, form=form)

	if current_app.wok.cases_count(current_user) >= current_app.config.get("LIMIT_NUM_CASES", 100):
		flash("""There is a limit on the number of simultaneous analysis that can be managed.
		You must remove finished analysis before running new ones.""", "error")
		return redirect(url_for("cases.index"))

	mutations_file = request.files['mutations_file']
	file_name = os.path.basename(mutations_file.filename)

	project_id = request.form['project_name']
	if len(project_id) == 0:
		project_id = os.path.splitext(file_name)[0]

	project_id = unique_project_id(normalize_id(project_id))

	'''
	if not current_user.validated:
		flash("""You can not run an analysis with your data until you are completely registered.
		Please check your email and follow the instructions to validate this account.""", "error")
		flash("Meanwhile you can play with the included examples.")
		return redirect(url_for("examples"))
	'''

	cb = ConfigBuilder()
	cb.add_value("user_id", current_user.nick)
	cb.add_value("workspace", DEFAULT_WORKSPACE)
	cb.add_value("project.id", project_id)

	#case_name = "-".join([current_user.nick, project_id])
	#cb.add_value("wok.instance.name", case_name)

	results_path, project_path, project_temp_path = get_paths(project_id)

	if not current_user.is_anonymous():
		cb.add_value("website.user_id", current_user.nick)

	if type == SINGLE_TUMOR_ANALYSIS: #request.form.get("variants_only") == "1":
		cb.add_value("variants_only", True)
		cb.add_value("skip_oncodrivefm", True)
		cb.add_value("skip_oncodriveclust", True)

	try:
		threshold = request.form["ofm_genes_threshold"]
		if re.match(r"^[1-9]\d*%?$", threshold):
			cb.add_value(ONCODRIVEFM_GENES_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("[{}] Wrong form input: {}={}".format(
				current_user.nick, "ofm_genes_threshold", request.form.get("ofm_genes_threshold")))

	try:
		threshold = request.form["ofm_pathways_threshold"]
		if re.match(r"^[1-9]\d*%?$", threshold):
			cb.add_value(ONCODRIVEFM_PATHWAYS_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("[{}] Wrong form input: {}={}".format(
				current_user.nick, "ofm_pathways_threshold", reuqest.form.get("ofm_pathways_threshold")))

	try:
		threshold = int(request.form["oclust_genes_threshold"])
		if threshold >= 1:
			cb.add_value(ONCODRIVECLUST_GENES_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("[{}] Wrong form input: {}={}".format(
				current_user.nick, "oclust_genes_threshold", request.form.get("oclust_genes_threshold")))

	genes_filter_enabled = request.form.get('genes_filter_enabled') == "1"
	cb.add_value(ONCODRIVEFM_FILTER_ENABLED_KEY, genes_filter_enabled)
	cb.add_value(ONCODRIVECLUST_FILTER_ENABLED_KEY, genes_filter_enabled)
	if genes_filter_enabled:
		try:
			genes_filter_file = request.files['genes_filter_file']
			genes_filter_file_path = os.path.join(project_temp_path, "genes-filter.txt")
			genes_filter_file.save(genes_filter_file_path)
			if os.path.getsize(genes_filter_file_path) != 0:
				cb.add_value(ONCODRIVEFM_GENES_FILTER_KEY, genes_filter_file_path)
				cb.add_value(ONCODRIVECLUST_GENES_FILTER_KEY, genes_filter_file_path)
		except:
			current_app.logger.exception("Error retrieving genes filter from form")

	assembly = request.form.get("assembly", DEFAULT_ASSEMBLY).lower()

	project = dict(
		id=project_id,
		assembly=assembly,
		files=[file_name])

	projects = [init_project_files(project, check_paths=False)]
	cb.add_value("projects", projects)

	properties = dict(
		analysis_type=type,
		path=os.path.relpath(project_path, results_path))

	current_app.logger.info("[{}] Starting analysis {} ...".format(current_user.nick, project_id))

	case = current_app.wok.create_case(current_user, project_id, cb, PROJECT_NAME, MUTATIONS_FLOW_NAME,
									   properties=properties, start=False)

	engine_case = current_app.wok.engine.case(case.engine_name)

	#TODO use a background thread
	upload_files(current_app.logger, case.engine_name, engine_case.storages, projects, streams=[mutations_file.stream])

	current_app.logger.info("[{}] Analysis {} started on case {}...".format(
							current_user.nick, project_id, case.engine_name))

	engine_case.start()

	return redirect(url_for("cases.index", highlight=case.id))
