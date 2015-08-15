#!/usr/bin/env python

"""
Pool a group of mrna normal assays.

* Configuration parameters:

- The ones required by intogen.data.entity.EntityServer
- repositories.assay: The path to the repository where the assay data files are
- repositories.data: (optional) The path to the repository where data files are written. Default value = work_path
- overwrite: (optional) Overwrite already existing pool data files ?. Default value = no, skip them

* Input:

- mrna_normal_pool_ids: list of mrna normal pools (mrna.normal_pool) to process.

* Output:

- Entities: mrna.normal_pool updated with pooled data file
"""

import os
import numpy

from wok.task import Task
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types
from intogen.matrix import MatrixReader, MatrixWriter, MatrixRow

class MeanPoolMethod(object):
	
	def __init__(self):
		self.s = {}

	def process(self, row_name, value):
		if row_name not in self.s:
			s = self.s[row_name] = [0, 0]
		else:
			s = self.s[row_name]

		s[0] += 1
		s[1] += value

	def pooled_rows(self):
		for row_name, s in sorted(self.s.items()):
			mean = s[1] / s[0]
			yield MatrixRow(row_name, [mean])

	def __repr__(self):
		sb = []
		for k, s in sorted(self.s.items()):
			sb += ["%s\t%.2f\t%.2f\t%.2f\n" % (k, s[0], s[1], s[1] / s[0])]
		return "".join(sb)

def run(task):
	
	# Initialization

	task.check_conf(["entities", "repositories", "repositories.assay"])
	conf = task.conf

	log = task.logger()
	
	task.check_in_ports(["normal_pool_ids"])

	normal_pool_port = task.ports["normal_pool_ids"]
	
	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)
	
	# Run

	log.info("Processing %i mrna normal pools ..." % normal_pool_port.size())

	for pool_id in normal_pool_port:
		pool = em.find(pool_id, types.MRNA_NORMAL_POOL)
		if pool is None:
			log.error("%s not found: %s" % (types.MRNA_NORMAL_POOL, pool_id))
			continue

		mf = pool.missing_fields(["study_id", "platform_id", "icdo_topography", "size", "mrna_absi_ids"])
		if len(mf) > 0:
			log.error("Normal pool %s missing required fields: %s {%s}" % (pool_id, mf, pool.get("__doc_path", "")))
			continue

		key = (pool["study_id"], pool["platform_id"], pool["icdo_topography"])
		log.info("Normal pool (%s) [%s] with %i assays ..." % (", ".join(key), pool_id, pool["size"]))

		data_file_path = types.MRNA_NORMAL_POOL.replace(".", "/")
		data_file_name = pool_id + ".tsv.gz"
		dst_rel_path = os.path.join(data_file_path, data_file_name)
		#dst_path = os.path.join(conf["repo.data"], dst_rel_path)

		if not overwrite and data_repo.exists(dst_rel_path) \
			and "mrna_absi_ids" in pool and "pooled_assays" in pool and \
					len(pool["mrna_absi_ids"]) == pool.get("pooled_assays", dtype=int):
			log.warn("Skipping normal pool %s that already has data" % pool_id)
			continue

		method = MeanPoolMethod()

		pooled_assays = 0
		duplicated_rows = False
		for absi in em.iter_all(types.MRNA_ABS_INTENSITY, eids = pool["mrna_absi_ids"]):
			mf = absi.missing_fields(["data_file/path", "data_file/name"])
			if len(mf) > 0:
				log.error("Normal assay %s missing required fields: %s {%s}" % (absi["id"], mf, absi.get("__doc_path", "")))
				continue

			data_file = absi["data_file"]
			rel_path = os.path.join(data_file["path"], data_file["name"])
			#filename = os.path.join(conf["repo.assays"], rel_path)
			repo = rs.repository(data_file["repo"])
			if not repo.exists(rel_path):
				log.error("File not found: %s" % rel_path)
				continue

			log.debug("Processing normal assay %s for source assay %s at %s ..." % (absi["id"], absi["assay_id"], rel_path))

			pooled_assays += 1
			
			mr = MatrixReader(repo.open_reader(rel_path))
			header = mr.read_header()
			if len(header.columns) != 2:
				log.error("Unexpected number of columns: %i" % len(header.columns))
				mr.close()
				continue

			row_names = set()
			for row in mr:
				if row.name in row_names:
					log.error("Skipping normal assay, duplicated row %s at file %s" % (row.name, rel_path))
					duplicated_rows = True
					break
				else:
					row_names.add(row.name)

				value = numpy.exp2(row.values[0])
				method.process(row.name, value)

			mr.close()

		if not duplicated_rows and pooled_assays > 0:
			exists = data_repo.exists(dst_rel_path)
			msg = {True : "Overwritting", False : "Writting"}[exists]
			log.debug("%s pooled data to %s ..." % (msg, dst_rel_path))

			mw = MatrixWriter(data_repo.open_writer(dst_rel_path))
			mw.write_header(["id", "value"])
			for row in method.pooled_rows():
				value = numpy.log2(row.values[0])
				mw.write(row.name, [value])
			mw.close()

			pool["pooled_assays"] = pooled_assays
			pool["data_file/repo"] = "data"
			pool["data_file/path"] = data_file_path
			pool["data_file/name"] = data_file_name
			em.persist(pool, types.MRNA_NORMAL_POOL)

	em.close()

	return 0

if __name__ == "__main__":
	Task(run).start()
