from wok.task import task

from intogensm import so
from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb
from intogensm.projects.results import ProjectResults
from intogensm.oncodrivefm import OncodriveFm


def increment(d, key):
	if key not in d:
		d[key] = 1
	else:
		d[key] += 1

def distrib(counts):
	d = {}
	for key, count in counts.items():
		increment(d, count)
	return [v for v in sorted(d.items(), key=lambda v: v[0])]

def quality_control(log, config, project, ofm):

	ofm.load_expression_filter()
	filter = ofm.filter if ofm.filter_enabled else None

	data = {}

	projdb = ProjectDb(project["db"])

	for csq in projdb.consequences(join_samples=True, join_ctypes=True):#,
								   #filters={ProjectDb.CSQ_CTYPES : so.ONCODRIVEFM}):
		
		is_selected = so.match(csq.ctypes, so.ONCODRIVEFM)
		
		var = csq.var
		for sample in var.samples:
			key = (sample.id, csq.gene)
			if key not in data:
				data[key] = is_selected
			else:
				data[key] = data[key] or is_selected

	projdb.close()

	source_genes = {}

	selected_genes = set()
	filter_genes = set()
	threshold_genes = set()

	selected_gene_sample_count = {} # number of samples for each selected gene
	filter_gene_sample_count = {} # number of samples per gene

	source_samples = {}
	selected_samples = set()
	filter_samples = set()
	threshold_samples = set()

	for (sample, gene), is_selected in data.items():
		if sample in source_samples:
			sample_index = source_samples[sample]
		else:
			source_samples[sample] = sample_index = len(source_samples)

		if is_selected:
			selected_samples.add(sample_index)

			increment(selected_gene_sample_count, gene)

	ofm.load_samples_thresholds(len(selected_samples))
	samples_threshold = ofm.genes_samples_threshold

	for (sample, gene), is_selected in data.items():
		if gene not in source_genes:
			source_genes[gene] = len(source_genes)

		gi = source_genes[gene]
		sample_index = source_samples[sample]

		if is_selected:
			if filter is None or filter.valid(gene):
				filter_samples.add(sample_index)

				increment(filter_gene_sample_count, gi)

				if selected_gene_sample_count[gene] >= samples_threshold:
					threshold_samples.add(sample_index)

	for gene, sample_count in selected_gene_sample_count.items():
		gi = source_genes[gene]

		selected_genes.add(gi)

		if filter is None or filter.valid(gene):
			filter_genes.add(gi)

			if sample_count >= samples_threshold:
				threshold_genes.add(gi)

	# significance of q-values

	projdb = ProjectDb(project["db"])
	sig_thresholds = [0.0, 0.001, 0.005] + [i / 100.0 for i in range(1, 11)] + [1.0]
	sig_count = [0] * len(sig_thresholds)
	for gene in projdb.genes():
		if gene.id in source_genes and source_genes[gene.id] in threshold_genes:
			i = 0
			while i < len(sig_thresholds) and gene.fm_qvalue > sig_thresholds[i]:
				i += 1

			for j in range(i, len(sig_count)):
				sig_count[j] += 1

	projdb.close()

	source_samples_count = len(source_samples)
	selected_samples_count = len(selected_samples)
	filter_samples_count = len(filter_samples)
	threshold_samples_count = len(threshold_samples)
	
	source_genes_count = len(source_genes)
	selected_genes_count = len(selected_genes)
	filter_genes_count = len(filter_genes)
	threshold_genes_count = len(threshold_genes)

	sorted_filter_genes = sorted(filter_genes, reverse=True, key=lambda gi: filter_gene_sample_count[gi])

	qc_data = dict(
			source=dict(
				genes=sorted(source_genes.keys(), key=lambda k: source_genes[k]),
				genes_count=source_genes_count,
				genes_lost_count=max(0, source_genes_count - threshold_genes_count),
				samples=sorted(source_samples.keys(), key=lambda k: source_samples[k]),
				samples_count=source_samples_count),
				samples_lost_count=max(0, source_samples_count - threshold_samples_count),
			selected=dict(
				genes=sorted(selected_genes),
				genes_count=selected_genes_count,
				genes_lost=sorted(set(source_genes.values()) - selected_genes),
				genes_lost_count=max(0, source_genes_count - selected_genes_count),
				samples=sorted(selected_samples),
				samples_count=selected_samples_count,
				samples_lost=sorted(set(source_samples.values()) - selected_samples),
				samples_lost_count=max(0, source_samples_count - selected_samples_count)),
			filter=dict(
				genes=sorted_filter_genes,
				genes_count=filter_genes_count,
				genes_lost=sorted(selected_genes - filter_genes),
				genes_lost_count=max(0, selected_genes_count - filter_genes_count),
				genes_sample_count=[filter_gene_sample_count[gi] for gi in sorted_filter_genes],
				samples=sorted(filter_samples),
				samples_count=filter_samples_count,
				samples_lost=sorted(selected_samples - filter_samples),
				samples_lost_count=max(0, selected_samples_count - filter_samples_count)),
			threshold=dict(
				genes=sorted(threshold_genes),
				genes_count=threshold_genes_count,
				genes_lost=sorted(filter_genes - threshold_genes),
				genes_lost_count=max(0, filter_genes_count - threshold_genes_count),
				samples=sorted(threshold_samples),
				samples_count=threshold_samples_count,
				samples_threshold=samples_threshold,
				samples_lost=sorted(filter_samples - threshold_samples),
				samples_lost_count=max(0, filter_samples_count - threshold_samples_count)),
			results=dict(
				sig_thresholds=sig_thresholds[1:],
				sig_count=sig_count[1:])
			)

	return qc_data

@task.foreach()
def oncodrivefm(project):
	log = task.logger
	conf = task.conf

	log.info("--- [{0}] --------------------------------------------".format(project["id"]))

	config = GlobalConfig(conf)
	paths = PathsConfig(config) # avoid that project conf override path configurations
	config = GlobalConfig(conf, project["conf"])

	ofm = OncodriveFm(config.oncodrivefm, paths, log)

	log.info("Calculating quality indicators for OncodriveFM ...")

	qc_data = quality_control(log, config, project, ofm)

	project_results = ProjectResults(project)
	project_results.save_quality_control("oncodrivefm", qc_data)

task.run()