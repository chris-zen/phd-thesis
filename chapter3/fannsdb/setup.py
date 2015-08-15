"""
Functional Scores Database
==========================
"""

#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup, find_packages

from fannsdb import VERSION, AUTHORS, AUTHORS_EMAIL

setup(
	name = "fannsdb",
	version = VERSION,
	packages = find_packages(),

	install_requires = [
		"pymongo",
		"bgcore>=0.3.2",
	],

	scripts = [
		"bin/ensembl-get-ann",
		#"bin/get-dbnsfp-prot-map-v64"
	],

	entry_points = {
		'console_scripts': [
			#'fannsdb-create = fannsdb.command.create:main',
			#'fannsdb-pred-list = fannsdb.command.pred_list:main',
			#'fannsdb-pred-update = fannsdb.command.pred_update:main',
			#'fannsdb-ann-list = fannsdb.command.ann_list:main',
			#'fannsdb-ann-add = fannsdb.command.ann_add:main',
			#'fannsdb-ann-rm = fannsdb.command.ann_rm:main',
			#'fannsdb-import = fannsdb.command.import:main',
			#'fannsdb-update = fannsdb.command.update:main',
			#'fannsdb-transform = fannsdb.command.transform:main',
			#'fannsdb-export = fannsdb.command.export:main',
			#'fannsdb-index = fannsdb.command.index:main',
			#'fannsdb-fetch = fannsdb.command.fetch:main',

			'dbnsfp-export = fannsdb.command.dbnsfp_export:main'
		]
	},

	# metadata for upload to PyPI
	author = AUTHORS,
	author_email = AUTHORS_EMAIL,
	description = "fannsdb",
	license = "UPF Free Source Code",
	keywords = "",
	url = "https://bitbucket.org/bbglab/fannsdb",
	long_description = __doc__,

	classifiers = [
		"Development Status :: 4 - Beta",
		"Intended Audience :: Bioinformatics",
		"Environment :: Console",
		"Intended Audience :: Science/Research",
		"Natural Language :: English",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2.7",
		"Topic :: Scientific/Engineering",
		"Topic :: Scientific/Engineering :: Bio-Informatics"
	]
)
