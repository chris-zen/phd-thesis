import re

from intogen.exception import PartialError
from intogen.repository import decompose_url
from intogen.repository import rpath

def skip_file(overwrite, repo, path, prev_url, source_files=None, repo_server=None):
	if overwrite:
		return False

	if prev_url is None:
		return False

	r, p = decompose_url(prev_url)
	p = rpath.absolute(p)
	path = rpath.absolute(path)

	if repo.name() != r or path != p:
		return False
	
	if repo.exists(path):
		#TODO compare source mtime with path ctime
		#TODO check whether it is partial or completed
		return True

	return False

# deprecated
def url_from_file_element(e):
	if e is None:
		return None

	if "repo" not in e:
		return None

	repo = e["repo"]

	path = e.get("path", "")
	if len(path) == 0 or path[0] != "/":
		path = "/" + path

	if "file" in e:
		return "{0}:{1}/{2}".format(repo, path, e["file"])
	else:
		return "{0}:{1}".format(repo, path)

QUOTED_PAT = re.compile(r'^"(.*)"$')
def remove_quotes(s):
	m = QUOTED_PAT.match(s)
	if m is not None:
		s = m.group(1)
	return s

def header_indices(names):
	map = {}
	for index, name in enumerate(names):
		map[name] = index
	return map

_ICDO_TOPOGRAPHY_PAT = re.compile(r"^(C\d\d)(.\d)?$")
_ICDO_MORPHOLOGY_PAT = re.compile(r"^\d\d\d\d(/\d)?$")
def classify_by_experiment_and_icdo(study_id, platform_id, icdo_topography, icdo_morphology):
	keys = []

	m = _ICDO_TOPOGRAPHY_PAT.match(icdo_topography)
	if m is None:
		raise PartialError("Wrong ICD-O Topography code: {}".format(icdo_topography))
	else:
		level1 = m.group(1)
		level2 = m.group(2)

	if len(icdo_morphology) > 0:
		m = _ICDO_MORPHOLOGY_PAT.match(icdo_morphology)
		if m is None:
			raise PartialError("Wrong ICD-O Morphology code: {}".format(icdo_morphology))

	keys += [(study_id, platform_id, level1, "")]
	if len(icdo_morphology) > 0:
		keys += [(study_id, platform_id, level1, icdo_morphology)]
		#keys += [(study_id, platform_id, "", icdo_morphology)]

	if level2 is not None:
		keys += [(study_id, platform_id, icdo_topography, "")]
		if len(icdo_morphology) > 0:
			keys += [(study_id, platform_id, icdo_topography, icdo_morphology)]

	return keys

def extract_from_entities(log, em, etype, *info_sets):

	log.info("Reading '{}' ...".format(etype))

	count = 0
	for id in em.find_ids(etype):
		e = em.find(id, etype)
		if e is None:
			log.error("{} not found: {}".format(etype, id))
			continue

		log.debug("{} [{}]".format(etype, id))

		for iset in info_sets:
			bag = iset[0]
			keys = iset[1]
			if not isinstance(keys, tuple):
				keys = tuple([keys])
			values = [e[k] for k in keys]
			bag.add(tuple(values))

		count += 1

	log.info("{} entities found".format(count))