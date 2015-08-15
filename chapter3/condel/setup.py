"""
Condel
========
"""

#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup, find_packages

from condel import VERSION, AUTHORS, AUTHORS_EMAIL
	
setup(
	name = "Condel",
	version = VERSION,
	packages = find_packages(),

	install_requires = [
		"bgcore>=0.3.1",
	],

	scripts = [
		#"bin/condel-ann-add",
		#"bin/condel-ann-get"
	],

	entry_points = {
		'console_scripts': [
			#'condel-training-sets = condel.command.training_sets:main',
			#'condel-weights = condel.command.weights:main',
			#'condel-plot-stats = condel.command.plot_stats:main',
			#'condel-plot-roc = condel.command.plot_roc:main',
			#'condel-calc = condel.command.calc:main',
			#'condel-calc-label = condel.command.calc_label:main'
		]
	},

	# metadata for upload to PyPI
	author = AUTHORS,
	author_email = AUTHORS_EMAIL,
	description = "Condel",
	license = "UPF Free Source Code",
	keywords = "",
	url = "https://bitbucket.org/bbglab/condel",
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
