import os

from flask import Blueprint, current_app, request, session, redirect, url_for, render_template, abort

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.config import ConfigBuilder

from intogensm.paths import get_project_path, get_temp_path, get_examples_path

from intogensm.common import project_analysis

from constants import COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS

bp = Blueprint("examples", __name__)

@bp.route("/<type>")
@login_required
def run(type):
	if type not in [COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS]:
		abort(400)

	'''
	if g.demo and current_user.max_analysis != -1 and proj_manager.get_projects_count(g.conn, g.user_id) >= current_user.max_analysis:
		flash("""The online version is for demo only and there is a limit for the number of simultaneous analysis a user can manage.
		You must remove finished analysis before running new ones.
		Please download the pipeline and install in your system to avoid these limitations.""", "error")
		return redirect(url_for("download"))
	'''

	cb = ConfigBuilder(current_app.wok.conf_builder)
	cb.add_value("workspace", "default")

	conf = cb.get_conf()

	results_path = os.path.join(conf["results_path"], current_user.nick)
	cb.add_value("results_path", results_path)

	temp_path = os.path.join(conf["temp_path"], current_user.nick)
	cb.add_value("temp_path", temp_path)

	if not current_user.is_anonymous():
		cb.add_value("website.user_id", current_user.nick)

	if type == COHORT_ANALYSIS:
		project_id = "cohort-example"
		mutations_path = get_examples_path(conf, "meduloblastoma_cohort_tier1.muts")
	elif type == SINGLE_TUMOR_ANALYSIS:
		project_id = "single-tumor-example"
		mutations_path = get_examples_path(conf, "pat4_crc.muts")
		cb.add_value("variants_only", True)
		cb.add_value("skip_oncodrivefm", True)
		cb.add_value("skip_oncodriveclust", True)

	i = 0
	base_id = project_id
	while current_app.wok.exists_case(current_user, project_id):
		i += 1
		project_id = "{}-{}".format(base_id, i)

	cb.add_value("project.id", project_id)

	conf = cb.get_conf()

	project_path = get_project_path(conf, project_id)
	if not os.path.exists(project_path):
		os.makedirs(project_path)

	project_temp_path = get_temp_path(conf, project_id)
	if not os.path.exists(project_temp_path):
		os.makedirs(project_temp_path)

	assembly = "hg19"

	cb, flow_uri = project_analysis(
		mutations_path,
		assembly=assembly,
		conf_builder=cb)

	properties = dict(
		analysis_type=type,
		path=project_path,
		temp_path=project_temp_path,
		data_file=mutations_path)

	current_app.logger.info("[{}] Starting example {} ...".format(
							current_user.nick, project_id))

	case = current_app.wok.create_case(current_user, project_id, cb, flow_uri,
									   properties=properties, start=True)

	current_app.logger.info("[{}] Example {} started on case {}...".format(
							current_user.nick, project_id, case.engine_name))

	return redirect(url_for("cases.index", highlight=case.id))