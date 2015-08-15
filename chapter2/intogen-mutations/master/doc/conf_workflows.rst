.. _conf_workflows:

Workflows configuration
+++++++++++++++++++++++

The following configuration parameters are available:

local_temp_path
---------------
**Type:** string. **Default:** system temporary directory. **Commands:** all commands

Path for local temporary files.

local_temp_remove
-----------------
**Type:** boolean. **Default:** true. **Commands:** all commands

Whether to remove or not local temporary files.

shared_temp_remove
------------------
**Type:** boolean. **Default:** true. **Commands:** all commands

Whether to remove or not shared temporary files.

vep_partition_size
------------------
**Type:** integer. **Default:** 100. **Commands:** project, projects

Maximum number of variants per *variant_effect_predictor* execution. Bigger values require more memory and decreases the number of partitions that will be run. Use a small value for laptops and bigger for workstations.

consequences_overwrite
----------------------
**Type:** boolean. **Default:** true. **Commands:** project, projects

If consequences has been already calculated whether to calculate again or not. This is an experimental parameter and should be used with caution.

skip_recurrences
----------------
**Type:** boolean. **Default:** false. **Commands:** project, projects

Skip calculation of project recurrences.

skip_oncodrivefm
----------------
**Type:** boolean. **Default:** false. **Commands:** project, projects

Skip OncodriveFM analysis.

skip_oncodriveclust
-------------------
**Type:** boolean. **Default:** false. **Commands:** project, projects

Skip OncodriveCLUST analysis.

oncodrivefm.genes.num_samplings
-------------------------------
**Type:** integer. **Default:** 10000. **Commands:** project, projects. **Levels**: global, project.

Number of samplings for the bootstrapping of genes.

oncodrivefm.genes.threshold
---------------------------
**Type:** string. **Default:** 1%. **Commands:** project, projects. **Levels**: global, project.

Threshold for the minimum number of mutations per gene to compute OncodriveFM. It can be a number representing the number of mutations or a percent representing a proportion of the number of samples.

oncodrivefm.genes.filter_enabled
-----------------------------------
**Type:** boolean. **Default:** True. **Commands:** project, projects. **Levels**: global, project.

Whether to use or not the genes filter.

oncodrivefm.genes.filter
------------------------
**Type:** path. **Default:** data/gene-filter.txt. **Commands:** project, projects. **Levels**: global, project.

Choose a different file with filters for OncodriveFM input genes.

The file contains one Ensembl gene identifier per line. Excluded genes are preceded by '-'. Examples:

1) Include only these genes::

	ENSG00000002726
	ENSG00000012223
	ENSG00000091831
	ENSG00000116299

2) Include all but the following genes::

	-ENSG00000002726
	-ENSG00000012223

oncodrivefm.pathways.num_samplings
----------------------------------
**Type:** integer. **Default:** 10000. **Commands:** project, projects. **Levels**: global, project.

Number of samplings for the bootstrapping of pathways.

oncodrivefm.pathways.threshold
------------------------------
**Type:** integer. **Default:** 10. **Commands:** project, projects. **Levels**: global, project.

Threshold for the minimum number of mutations per pathway to compute OncodriveFM.

oncodrivefm.estimator
---------------------
**Type:** string. **Default:** mean. **Commands:** project, projects. **Levels**: global, project.

Test estimator for OncodriveFM computation. Posssible values: mean, median

oncodrivefm.num_cores
---------------------
**Type:** integer. **Default:** 1. **Commands:** project, projects. **Levels**: global, project.

Define the maximum number of cores to use for OncodriveFM computation.

oncodriveclust.mutations_threshold
----------------------------------
**Type:** integer. **Default:** 5. **Commands:** project, projects. **Levels**: global, project.

Threshold for the minimum number of mutations of a gene to be included in the OncodriveCLUST analysis.

oncodriveclust.genes_filter_enabled
-----------------------------------
**Type:** boolean. **Default:** True. **Commands:** project, projects. **Levels**: global, project.

Whether to use or not the genes filter.

oncodriveclust.genes_filter
---------------------------
**Type:** path. **Default:** data/gene-filter.txt. **Commands:** project, projects. **Levels**: global, project.

Choose a different file with filters for OncodriveCLUST input genes. See `oncodrivefm.genes.filter`_.

combination.classifiers
-----------------------
**Type:** list of dictionaries. **Commands:** project, projects, combination.

Required to compute combinations for recurrences, OncodriveFM and OncodriveCLUST.

Example:

.. sourcecode:: json

    {
    	"combination" : {
    		"classifiers" : [
    			{
    				"id"                    : "cancer_site",
    				"name"                  : "Cancer site",

    				"keys"                  : ["cancer_site_id"],
    				"default_key_values"    : ["undefined"],

    				"short_names"           : ["cancer_site_code"],
    				"default_short_values" 	: ["undefined"],

    				"long_names"            : ["cancer_site_name"],
    				"default_long_values"   : ["undefined"]
    			},
    			{
    				"id"                    : "global",
    				"name"                  : "Global",

    				"keys"                  : ["___"],
    				"default_key_values"    : ["all"]
    			}
    		]
    	}
    }

project.annotations
-------------------
**Type**: list of either strings or tuples. **Default**: All project annotations. **Commands**: project, projects.

Define which annotations to include in project.tsv

Example:

.. sourcecode:: json

    [
        "source",
        "authors",
        ["cancer_site_code", "ICDO_CODE"],
        ["cancer_site_name", "ICDO_NAME"]
    ]

website.templates_path
----------------------

Path for website templates.

website.projects_list
---------------------

Path to the file defining the list of projects for the website server.
