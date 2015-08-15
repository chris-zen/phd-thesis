"""
IntOGen Mutations Analysis library
==================================
"""

from setuptools import setup, find_packages

from intogensm import VERSION, AUTHORS, CONTACT

setup(
	name = "intogensm",
	version = VERSION,
	packages = find_packages(),

	install_requires = [
		"SQLAlchemy==0.8.2",
		"requests==1.1.0",
		"Sphinx==1.2",
		"blinker==1.3",
		"Flask==0.10.1",
		"Flask-Login==0.2.8"
	],

	scripts = [
	],

	entry_points = {
		'console_scripts': [
		]
	},

	# metadata for upload to PyPI
	author = AUTHORS,
	author_email = CONTACT,
	description = "IntOGen Mutations Analysis library",
	license = "UPF Free Source Code",
	keywords = "mutation,variant,analysis,pipeline,driver,gene,genome",
	url = "https://www.intogen.org",
	long_description = __doc__,

	classifiers = [
		"Development Status :: 5 - Production/Stable",
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
