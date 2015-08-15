import os
import re

from flask import Blueprint, g, current_app, request, session, redirect, url_for, render_template, abort, flash

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.config import ConfigBuilder

from intogensm.utils import normalize_id
from intogensm.paths import get_project_path, get_temp_path
from intogensm.constants.oncodrivefm import ONCODRIVEFM_GENES_THRESHOLD, ONCODRIVEFM_PATHWAYS_THRESHOLD
from intogensm.constants.oncodriveclust import ONCODRIVECLUST_MUTATIONS_THRESHOLD

from intogensm.common import project_analysis

from constants import *

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

	mutations_file = request.files['mutations_file']
	file_name = os.path.basename(mutations_file.filename)

	project_id = request.form['project_name']
	if len(project_id) == 0:
		project_id = os.path.splitext(file_name)[0]

	project_id = normalize_id(project_id)

	i = 0
	base_id = project_id
	while current_app.wok.exists_case(current_user, project_id):
		i += 1
		project_id = "{}-{}".format(base_id, i)

	'''
	if current_app.wok.exists_case(current_user, project_id):
		flash("An analysis with this name already exists. Please give it a different name or remove the previous one before starting again.", "error")
		return render_template("analysis.html", type=type, form=request.form)
	'''

	'''
	if g.demo and current_user.max_analysis != -1 and proj_manager.get_projects_count(g.conn, g.user_id) >= current_user.max_analysis:
		flash("""The online version is for demo only and there is a limit for the number of simultaneous analysis a user can manage.
		You must remove finished analysis before running new ones.
		Please download the pipeline and install in your system to avoid these limitations.""", "error")
		return redirect(url_for("download"))

	if not current_user.validated:
		flash("""You can not run an analysis with your data until you are completely registered.
		Please check your email and follow the instructions to validate this account.""", "error")
		flash("Meanwhile you can play with the included examples.")
		return redirect(url_for("examples"))
	'''

	cb = ConfigBuilder(current_app.wok.conf_builder)
	cb.add_value("workspace", "default")
	cb.add_value("project.id", project_id)

	#case_name = "-".join([current_user.nick, project_id])
	#cb.add_value("wok.instance.name", case_name)

	conf = cb.get_conf()

	results_path = os.path.join(conf["results_path"], current_user.nick)
	cb.add_value("results_path", results_path)

	temp_path = os.path.join(conf["temp_path"], current_user.nick)
	cb.add_value("temp_path", temp_path)

	conf = cb.get_conf()

	project_path = get_project_path(conf, project_id)
	if not os.path.exists(project_path):
		os.makedirs(project_path)

	project_temp_path = get_temp_path(conf, project_id)
	if not os.path.exists(project_temp_path):
		os.makedirs(project_temp_path)

	if not current_user.is_anonymous():
		cb.add_value("website.user_id", current_user.nick)

	# FIXME ? type == SINGLE_TUMOR_ANALYSIS
	if request.form.get("variants_only") == "1":
		cb.add_value("variants_only", True)
		cb.add_value("skip_oncodrivefm", True)
		cb.add_value("skip_oncodriveclust", True)

	try:
		threshold = request.form["ofm_genes_threshold"]
		if re.match(r"^[1-9]\d*%?$", threshold):
			cb.add_value(ONCODRIVEFM_GENES_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("Undefined form input: {}".format("ofm_genes_threshold"))

	try:
		threshold = request.form["ofm_pathways_threshold"]
		if re.match(r"^[1-9]\d*%?$", threshold):
			cb.add_value(ONCODRIVEFM_PATHWAYS_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("Undefined form input: {}".format("ofm_pathways_threshold"))

	try:
		threshold = int(request.form["oclust_genes_threshold"])
		if threshold >= 1:
			cb.add_value(ONCODRIVECLUST_GENES_THRESHOLD_KEY, threshold)
	except:
		if type == COHORT_ANALYSIS:
			current_app.logger.warn("Undefined form input: {}".format("oclust_genes_threshold"))

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

	mutations_path = os.path.join(project_temp_path, file_name)
	try:
		mutations_file.save(mutations_path)
	except:
		current_app.logger.exception("Error while saving mutations file {} into {}".format(mutations_file.filename, mutations_path))
		flash("""There were some problem with the input file for mutations.
			Please check that a file has been loaded before submitting a new analysis.
			This error has been already submitted to the application administrators
			who will take care of it as soon as possible.""")
		return render_template("analysis.html", type=type, form=request.form)

	assembly = request.form.get("assembly", "hg19").lower()

	cb, flow_uri = project_analysis(
				mutations_path,
				assembly=assembly,
				conf_builder=cb)

	properties = dict(
		analysis_type=type,
		path=project_path,
		temp_path=project_temp_path,
		data_file=mutations_path)

	current_app.logger.info("[{}] Starting analysis {} ...".format(
							current_user.nick, project_id))

	case = current_app.wok.create_case(current_user, project_id, cb, flow_uri,
									   properties=properties, start=True)

	current_app.logger.info("[{}] Analysis {} started on case {}...".format(
							current_user.nick, project_id, case.engine_name))

	return redirect(url_for("cases.index", highlight=case.id))
