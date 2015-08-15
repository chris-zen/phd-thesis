"""
TransFIC
========
"""

#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup, find_packages

from transfic import VERSION, AUTHORS, AUTHORS_EMAIL
	
setup(
	name = "TransFIC",
	version = VERSION,
	packages = find_packages(),

	install_requires = [
		"bgcore>=0.3.1",
	],

	scripts = [
		"bin/transfic-perf-init",
		"bin/transfic-perf-scores",
	],

	entry_points = {
		'console_scripts': [
			'transfic-obo-to-map = transfic.command.obo_to_map:main',
			'transfic-vcf-to-snvs = transfic.command.vcf_to_snvs:main',
			'transfic-filter-transcripts = transfic.command.filter_transcripts:main',
			'transfic-esp6500-to-snvs = transfic.command.esp6500_to_snvs:main',
			'transfic-blt-partial = transfic.command.blt_partial:main',
			'transfic-blt-groups = transfic.command.blt_groups:main',
			'transfic-calc = transfic.command.calc:main',
			'transfic-calc-label = transfic.command.calc_label:main',
			'transfic-perf-plot = transfic.command.perf_plot:main',
			'transfic-perf-cosmic = transfic.command.perf_cosmic:main',
			'transfic-perf-cosmic52 = transfic.command.perf_cosmic52:main',
			'transfic-cutoffs = transfic.command.cutoffs:main',
			'transfic-cutoffs-plot = transfic.command.cutoffs_plot:main'
		]
	},

	# metadata for upload to PyPI
	author = AUTHORS,
	author_email = AUTHORS_EMAIL,
	description = "TransFIC",
	license = "UPF Free Source Code",
	keywords = "",
	url = "https://bitbucket.org/bbglab/transfic",
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
