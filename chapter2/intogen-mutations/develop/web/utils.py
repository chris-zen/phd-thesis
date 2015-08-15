from flask import current_app
from flask.ext.login import current_user

from intogensm.analysis import PROJECT_NAME, DEFAULT_PLATFORM_NAME
from intogensm.pathutils import ensure_path_exists
from intogensm.config.paths import get_project_path, get_results_path, get_temp_path

from constants import DEFAULT_WORKSPACE

def unique_project_id(project_id):
	i = 0
	base_id = project_id
	while current_app.wok.exists_case(current_user, project_id):
		i += 1
		project_id = "{}-{}".format(base_id, i)
	return project_id

def get_project_conf(platform=None):
	conf = current_app.wok.project_conf(PROJECT_NAME, platform_name=platform or DEFAULT_PLATFORM_NAME)
	conf["user_id"] = current_user.nick
	conf["workspace"] = DEFAULT_WORKSPACE
	return conf

def get_paths(project_id, conf=None):
	if conf is None:
		conf = get_project_conf()

	results_path = get_results_path(conf)
	project_path = get_project_path(conf, project_id)
	project_temp_path = get_temp_path(conf, project_id)
	ensure_path_exists(project_path)
	ensure_path_exists(project_temp_path)
	return results_path, project_path, project_temp_path