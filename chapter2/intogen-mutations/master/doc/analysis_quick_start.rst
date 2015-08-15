Quick start guide
=================

This guide will show you how to perform the analysis of one of the included examples using the terminal.

.. todo::

   For an example using the web interface see X.
   reference to running an example with web interface

Available examples
------------------

There are two examples included, one for each use case:

* **High-confidence somatic mutations identified across 37 medulloblastomas** (for a cohort analysis)

  `Robinson et al., Nature 488, 43–8 (2012) <http://www.nature.com/nature/journal/v488/n7409/full/nature11213.html>`_

  The IntOGen Mutations platform is the first tool that unites a pipeline to analyze the somatic mutations identified across a cohort of tumor samples with a web discovery tool containing accumulated knowledge on the role of somatic mutations in tumors obtained from systematic equivalent analysis of datasets of resequenced tumor genomes. Therefore, one important use of IntOGen Mutations is to identify likely driver genes across a cohort of tumors and compare them with the list of previously detected likely drivers in the same cancer site or in general that is provided by the IntOGen Mutations web discovery tool.

* **Somatic mutations detected in the exome of a metastatic colon cancer** (for a single tumor analysis)

  `Roychowdhury et al., Sci Transl Med 3, 111ra121 (2011); DOI: 10.1126/scitranslmed.3003161 <http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3476478/>`_

  The IntOGen Mutations pipeline can be used to rank the somatic mutations identified in the tumor of an individual patient. Researchers with a list of mutations detected in a tumor can identify functionally impacting mutations, find mutations affecting cancer driver genes, and identify any mutations in the patient that have been previously observed in tumors. All this information can help to suggest which genes might have driven tumorigenesis in the patient, with the final aim of informing a personalized approach to treatment.

Running an example
------------------

You can perform an analysis for one of the included examples just running the following command::

	$ ./run analysis -p cohort-example examples/meduloblastoma_cohort_tier1.muts

The *-p cohort-example* specifies the analysis identifier and it is used to name the results folder. The argument *examples/meduloblastoma_cohort_tier1.muts* specifies the file containing the mutations. If more than one file is specified then the workflow will merge all the mutations.

To perform a single tumor analysis just append the argument *--single-tumor** like in the following example::

	$ ./run analysis --single-tumor -p single-tumor-exampl./run analysis --single-tumor -p single-tumor-example examples/pat4_crc.mutse examples/pat4_crc.muts

The results will be under the folder *runtime/results/<user>/<workspace>/projects/<project>/results.zip*. Where *<user>* corresponds to the unix user name, *<workspace>* to the workspace (it is *default* if nothing specified) and *<project>* to the project identifier, in our example would be *cohort-example*.

It is possible to run many analysis with different identifiers. A workspace represents a group of projects organized together. To change the workspace you can use the argument *-w* like::

	$ ./run analysis -w examples -p cohort-example examples/meduloblastoma_cohort_tier1.muts./run analysis -w examples -p cohort-example examples/meduloblastoma_cohort_tier1.muts

The workflow splits mutations into partitions of a fixed size before running *VEP*, which requires more memory for higher number of mutations. In case you are running the analysis in a laptop with low memory you may configure the workflow to create smaller partitions. There is a configuration parameter called *vep_partition_size* (see :ref:`configuration` for a detailed list of the available configuration parameters) that can be adjusted using the following command line::

	$ ./run analysis -p cohort-example -D vep_partition_size=30 examples/meduloblastoma_cohort_tier1.muts

Many times you end passing always the same parameters and you don't want to type them all the time, so you could put them in a configuration file. The configuration files use the `JSON <http://en.wikipedia.org/wiki/JSON>`_ format and, as a convention in IntOGen Mutations, they have the *.conf* extension. As an example we can create *examples.conf* as::

	{
		"vep_partition_size" : 30,
		"oncodrivefm" : {
			"genes" : {
				"num_samplings" : 1000
			}
		}
	}

It is also possible to combine configuration files and definitions in the same command::

	$ ./run analysis -p cohort-example -C examples.conf -D wok.platform.jobs.max_cores=2 examples/meduloblastoma_cohort_tier1.muts

