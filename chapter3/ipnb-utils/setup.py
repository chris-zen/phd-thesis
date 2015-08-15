"""
Library with useful things for IPython Notebook
===============================================
"""

from setuptools import setup, find_packages

setup(
	name = "ipnp-utils",
	version = "0.1-dev",
	packages = find_packages(),

	install_requires = [
		#"ipython>=2.0.0",
		"pymongo"
	],

	dependency_links = [
		"git+https://github.com/ipython/ipython.git@1bf6e5d459a8bb4101e0a5da1d09c36412e37b22#egg=ipython-origin/HEAD"
	],

	scripts = [
	],

	entry_points = {
		'console_scripts': [
		]
	},

	# metadata for upload to PyPI
	author = "Christian Perez-Llamas",
	author_email = "chrispz@gmail.com",
	description = "Library with useful things for IPython Notebook",
	license = "BSD",
	keywords = "IPython",
	url = "https://github.com/chris-zen/ipnb-utils",
	long_description = __doc__,

	classifiers = [
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: BSD",
		"Natural Language :: English",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2.7"
	]
)
