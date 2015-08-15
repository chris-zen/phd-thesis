import os

from flask import Blueprint, current_app, request, session, redirect, url_for, render_template, abort, flash

from flask.ext.login import current_user, login_required, confirm_login, fresh_login_required

from wok.config import ConfigBuilder
from wok.logger import get_logger

from intogensm.config.paths import get_examples_path
from intogensm.analysis import PROJECT_NAME, MUTATIONS_FLOW_NAME, init_project_files, upload_files

from constants import COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS, DEFAULT_WORKSPACE
from utils import unique_project_id, get_project_conf, get_paths

bp = Blueprint("examples", __name__)

@bp.route("/<type>")
@login_required
def run(type):
	if type not in [COHORT_ANALYSIS, SINGLE_TUMOR_ANALYSIS]:
		abort(400)

	if current_app.wok.cases_count(current_user) >= current_app.config.get("LIMIT_NUM_CASES", 100):
		flash("""There is a limit on the number of simultaneous analysis that can be managed.
		You must remove finished analysis before running new ones.""", "error")
		return redirect(url_for("cases.index"))

	cb = ConfigBuilder()
	cb.add_value("user_id", current_user.nick)
	cb.add_value("workspace", DEFAULT_WORKSPACE)

	if not current_user.is_anonymous():
		cb.add_value("website.user_id", current_user.nick)

	conf = get_project_conf()

	if type == COHORT_ANALYSIS:
		project_id = "cohort-example"
		mutations_path = get_examples_path(conf, "meduloblastoma_cohort_tier1.muts")
	elif type == SINGLE_TUMOR_ANALYSIS:
		project_id = "single-tumor-example"
		mutations_path = get_examples_path(conf, "pat4_crc.muts")
		cb.add_value("variants_only", True)
		cb.add_value("skip_oncodrivefm", True)
		cb.add_value("skip_oncodriveclust", True)

	project_id = unique_project_id(project_id)

	cb.add_value("project.id", project_id)

	results_path, project_path, project_temp_path = get_paths(project_id, conf=conf)

	assembly = "hg19"

	project = dict(
		id=project_id,
		assembly=assembly,
		files=[mutations_path])
	projects = [init_project_files(project)]
	cb.add_value("projects", projects)

	properties = dict(
		analysis_type=type,
		path=os.path.relpath(project_path, results_path),
		data_file=mutations_path)

	current_app.logger.info("[{}] Starting example {} ...".format(current_user.nick, project_id))

	case = current_app.wok.create_case(current_user, project_id, cb, PROJECT_NAME, MUTATIONS_FLOW_NAME,
									   properties=properties, start=False)

	engine_case = current_app.wok.engine.case(case.engine_name)

	#TODO use a background thread
	upload_files(current_app.logger, case.engine_name, engine_case.storages, projects)

	current_app.logger.info("[{}] Example {} started on case {}...".format(
								current_user.nick, project_id, case.engine_name))

	engine_case.start()

	return redirect(url_for("cases.index", highlight=case.id))