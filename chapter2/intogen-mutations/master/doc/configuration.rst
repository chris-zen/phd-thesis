.. _conf:

Configuration
=============

Different components of this software can be configured in different ways. The *setup* script will create the basic configuration for the system but the user can override it or add more configuration values to adapt it to their preferences.

The workflows are configured with JSON files as this is the way that Wok, the workflow management system, works. On the other side the web server is configured with python files according to the Flask web microframework rules.

There are some differences depending on how it is used. When performing analyses from the command line the configuration is specified by passing configuration file paths or configuration parameters as options in the command line. For example, the following command will load a configuration file from *conf/specific_configuration.conf* and will configure *vep_partition_size* with the value *1000*::

	$ ./run analysis -C conf/specific_configuration.conf -D vep_partition_size=1000 -p test data.maf

Many *-C* and *-D* options can be specified. The right-most definitions override previous definitions, whether they are in files or command line. For example, if *specific_configuration.conf* was assigning the value *400* to *vep_partition_size*, the following *-D* definition overrides its value by *1000*.

In case that the web server is run, then the workflow configuration has to be defined through the enviroment variable WOK_EXTRA_CONF. For example, to specify that the configuration file *conf/specific_configuration.conf* has to be loaded you can run the server as::

	$ export WOK_EXTRA_CONF="specific_configuration"
	$ ./run service

Note that you can skip the folder when it is inside the default configuration folder *conf/* and the extension if is has the default *.conf* extension.

The configuration specific to the web server can be defined with the enviroment variable SM_EXTRA_CONF. For example::

	$ export SM_EXTRA_CONF="analytics"
	$ ./run service

This will load the file *conf/analytics.cfg* as the web server configuration.

Next there is documentation on how to configure the workflows and the web server:

.. toctree::
   :maxdepth: 2

   conf_workflows
   conf_web