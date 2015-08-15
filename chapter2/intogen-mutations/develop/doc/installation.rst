Installation
============

IntOGen Mutations can be used in different ways:

* **Online version**: There is an online version of the pipeline in our servers at http://www.intogen.org/mutations. Just click on **Analysis** in the top bar.

* **Local installation**: This allows to install and run it locally in your machines. You will need to run some commands in a terminal, therefore basic knowledge on Unix commands is required. You may need to install some required programs and libraries.

Online version
--------------

Go to http://www.intogen.org/mutations and click on **Analysis** in the top bar.

You need to register yourself in order to use IntOGen Mutations. User authentication is managed using `Mozilla Persona <https://login.persona.org/>`_ which allows to use the same identity across different web sites. Mozilla Persona makes the process of registration and sign-in very easy and fast.

To avoid overloading the system there are some limitations (only for the online version):

* A maximum of 4 analysis can be managed at the same time.
* Currently the maximum number of mutations is unlimited but may change in the future.
* The results of the analysis can be removed at any time without notice (for example due to a version update). We are working to avoid this inconvenience.

.. _local-installation:

Local installation
------------------

IntOGen Mutations can be installed locally on any computer running some flavour of Linux or Mac OS.

Downloading
'''''''''''

Please, read carefully the :ref:`license terms<license>`.

You can download it from any of the following branches:

* `Stable (recommended) <https://bitbucket.org/intogen/mutations-analysis/get/master.tar.gz>`_
* `Development <https://bitbucket.org/intogen/mutations-analysis/get/develop.tar.gz>`_

You can uncompress it and move inside the uncompressed folder with the following commands::

	$ tar -xvf intogen-mutations-analysis-dd316346f2cd.tar.gz
	$ cd intogen-mutations-analysis-dd316346f2cd

Note that the name of the file will change for different versions. Once uncompressed you can move to the next step.

Prerequisites
'''''''''''''

IntOGen Mutations is intended to work with Linux and Mac OS X. It depends on some unix commands, Python 2.7 or above and Perl 5.10 or above. It also requires some Python and Perl libraries to be installed, some of them are already included and the others are automatically installed by a *setup* script. Only in case you experiment problems with the automatic setup you will need to know which are the libraries, and install them manually (see :ref:`manual-setup`).

Setup
'''''

The following command will start the setup with the default options::

	$ ./setup

*setup* is an script that checks whether all the required programs and libraries are installed, downloads the required data and generates the configuration files. The Python required libraries are downloaded from internet and compiled automatically. The installer will also download the required data from different sources (VEP cache from Ensembl, Mutationassessor, and so on). This process could take quite long depending on your internet connection as it has to download nearly 3.5 Gb. There are several options you can pass to configure the setup process, just run the following command to know which options are available::

	$ ./setup --help

We can not check the installer on every possible computer configuration so it is possible that it fails to install everything automatically. The most critical part is the installation of some Python libraries such as numpy, scipy, pandas and statsmodels (as reported by some Mac OS users), so we have prepared this `Manual setup`_ guide that will elaborate more in the installation process and how to overcome possible problems.

To check that everything worked fine, just run the following command::

	$ ./run analysis --help

you should get something similar to::

	usage: run analysis [-h] [--version] [-w NAME] [-p NAME] [-a ASSEMBLY]
	                          [-L {debug,info,warn,error,critical,notset}]
	                          [-n NAME] [-c FILE] [-D PARAM=VALUE] [-j NUM]
	                          files [files ...]

	positional arguments:
	  files                 Variants files

	optional arguments:
	  -h, --help            show this help message and exit
	  --version             show program's version number and exit
	  -w NAME, --workspace NAME
	                        Define the workspace name.
	  -p NAME, --id NAME    Define the project identifier. Required.
	  -a ASSEMBLY, --assembly ASSEMBLY
	                        Define the assembly [hg18, hg19]. Default is hg19.
	  -L {debug,info,warn,error,critical,notset}, --log-level {debug,info,warn,error,critical,notset}
	                        Define the logging level

	Wok Options:
	  -n NAME, --instance NAME
	                        Define the instance name
	  -C FILE, --conf FILE  Load configuration from a file. Multiple files can be
	                        specified
	  -D PARAM=VALUE        Define configuration parameters.
	                        Multiple definitions can be specified.
	                        Example: -D option1=value
	  -j NUM                Define the maximum number of cores to use. Default all
	                        the cores available.

Web application
'''''''''''''''

Once you have installed and configured IntOGen Mutations (see :ref:`local-installation`) you can start an instance of the web application with just one command. There are two ways to launch it, the only difference between them is that one of them launches your browser with the url of the service.

The following command will start the service and immediately will launch your web browser::

 	$ ./run web

If you only want to start the service you can run the following command::

 	$ ./run service

There is an example of an Upstart configuration file (*upstart.conf*) in case you want the service to start whenever your computer starts. Upstart is a system to manage services in Unix that pretends to replace the old rc init scripts. It was mainly introduced by Ubuntu.

By default the service listens on port 5000, but this can be configured through the command line::

 	$ ./run service --port 6080

Run the following command to get more details on the available options::

 	$ ./run service --help

Read :ref:`conf` to know how to configure the system for your preferences.

.. _manual-setup:

Manual setup
''''''''''''

We use `virtualenv <http://www.virtualenv.org/>`_ to manage Python dependencies. *virtualenv* is a tool to create isolated *Python* environments. The basic problem being addressed is one of dependencies and versions, and indirectly permissions. With *virtualenv* you can install the libraries and programs without having to be *root* and without conflicting with other program's libraries.

The *setup* script checks whether *virtualenv* is installed in your system or not. If it is not installed it will use the *virtualenv* script included within the IntOGen Mutations package. It will create a virtual enviroment for all the dependencies under the runtime folder (by default on *runtime/env*) and then it will use `pip <http://www.pip-installer.org/>`_ to install the dependencies. This is one of the reasons why all the IntOGen Mutations commands have to be prefixed with *run*. One of the first things that *run* does is to activate the virtual enviroment.

The required Python libraries are:

* distribute 0.6.35
* requests 1.1.0
* Flask 0.10.1
* Flask-Login 0.2.7
* SQLAlchemy 0.8.2
* blinker 1.3
* Sphinx 1.2b1 or above
* pytz 2013b
* python-dateutil 2.1
* numpy 1.7.1
* scipy 0.12.0
* pandas 0.12.0
* statsmodels 0.4.3

plus some other Python programs and libraries developed by ourselves:

* `BgCore <https://bitbucket.org/bbglab/bgcore>`_
* `OncodriveFM <https://bitbucket.org/bbglab/oncodrivefm>`_
* `OncodriveCLUST <https://bitbucket.org/bbglab/oncodriveclust>`_

Some libraries (*numpy*, *scipy*, *pandas* and *statsmodels*) require to compile their code during the installation. Although the compilation is automatically done by *pip* it may not work as expected if some of the low level requisites are not satisfied:

- To have compilers for *C*, *C++* and *Fortran* installed in your system. It is common on Linux systems to have compilers for C and C++ already installed, so you usually may only need to install the fortran compiler. In the case of Mac OS you need to install XCODE [1]_ (you would be also interested in [2]_ and [3]_).
- To have installed *BLAS*, *LAPACK* or *ATLAS*. These are libraries for numerical computation required mainly by *scipy*. You will find more information on how to install *scipy* `here <http://www.scipy.org/Installing_SciPy>`_. If *scipy* doesn't find these libraries installed in the default locations (mainly because you have compiled and installed them manually) it requires some enviroment variables to be exported with their path. The *setup* script will source *conf/user.sh* if available just after the activation of the virtual enviroment.

The easiest way to overcome these issues is just to install them system wide using the package manager. For example, in Ubuntu you can install *python-numpy* and *python-scipy* (still *pandas* and *statsmodels* need to be compiled by *pip*)

The *setup* script have an option for including system libraries in the virtual enviroment (*--env-global*).

.. [1] https://developer.apple.com/technologies/tools/
.. [2] http://woss.name/2012/01/24/how-to-install-a-working-set-of-compilers-on-mac-os-x-10-7-lion/
.. [3] https://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man7/ATLAS.7.html
