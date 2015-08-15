import os
import logging

from bgcore import tsv

def add_map(db, id, name, type, priority, path, header=True):
	"""
	:param id: map identifier
	:param name: map name
	:param type: xref maps to type: transcript, protein
	:param path: map file
	:param priority: priority for translating input xrefs. 0 means not considered for translation. Default 0.
	:param header: specify that the map file have a header.
	"""

	logger = logging.getLogger("fannsdb.map-add")

	logger.info("Creating map {} ...".format(name))

	db.add_map(id, name, type, priority)

	logger.info("Loading items ...")

	with tsv.open(path) as f:
		for source, value in tsv.lines(f, (str, str), header=header):
			if len(source) > 0 and len(value) > 0:
				db.add_map_item(id, source, value)
