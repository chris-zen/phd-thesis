Changes
=======

2.4.0
-----
(*2013-10-25*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.4.0.tar.gz>`__

* Slight changes on how the functional impacts are calculated.
* Bug fix: Gene filter was always applied to OncodriveCLUST independently of the configuration.
* Bug fix: Parsing of insertions start position was shifted one base position for some cases.
* Bug fix: MAF parser not working well.
* Quality control reports for variants, OncodriveFM and OncodriveCLUST.
* New run commands: summary, qc, qc-report.
* Wok dependency updated to 3.0.0-rc3
* The web application can be run under a WSGI container such as Gunicorn.
* Several bug fixes and improvements.

2.3.0
-----
(*2013-09-15*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.3.0.tar.gz>`__

* Updated to the new version of Wok 3.0.0-rc2
* Now we distinguish between cohort analysis and single tumor analysis
* Name changes in the command line interface and new option --single-tumor for single tumor analysis
* Web interface completely redesigned and adapted for Wok 3.0.0-rc2

2.2.0
-----
(*2013-09-15*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.2.0.tar.gz>`__

* New column for Mutations with protein changes
* New impact category 'unknown' for splicing variants and when no MA, PPH2 or SIFT impact is available.
* Gene expression white-list filter added to OncodriveFM and OncodriveCLUST analysis
* New column with information on whether qvalue could not be calculated on OncodriveFM and OncodriveCLUST

2.1.1
-----
(*2013-05-08*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.1.1.tar.gz>`__

* New documentation system using Sphinx.
* New option in the web to analyse only for variants.
* Determine whether results have been already found in IntOGen Mutations and link them.

2.1.0
-----
(*2013-04-10*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.1.0.tar.gz>`__

* Improvements on the setup and new options --env-global and --develop
* OncodriveFM updated to 0.4. Now the mean estimator is used.
* OncodriveCLUST results completely integrated.
* Recurrences of mutations calculated for coding regions per variant-gene (Gene affected by a variant).
* Results only contain functional scores and TransFIC values for synonymous consequences.
* Web interface improvements: Projects automatic refresh, Button to Browse the results (only in the public demo).
* Fixed: Some MutationAssessor scores were missing due to reverse strand issues.

2.0.0
-----
(*2013-03-12*) `Download <https://bitbucket.org/intogen/mutations-analysis/get/2.0.0.tar.gz>`__

* Several improvements since 1.x
* Everything is written in Python now, there are still Perl dependencies because of variant_effect_predictor.pl
