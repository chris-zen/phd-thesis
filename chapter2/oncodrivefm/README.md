# OncodriveFM #

OncodriveFM  detects candidate cancer driver genes and pathways from catalogs of somatic mutations in a cohort of tumors by computing the bias towards the accumulation of functional mutations (FM bias).This novel approach avoids some known limitations of recurrence-based approaches, such as the difﬁculty to estimate background mutation rate, and the fact that they usually fail to identify lowly recurrently mutated driver genes.

## Installation ##

OncodriveFM depends on some external libraries, [numpy](http://www.numpy.org/), [scipy](http://www.scipy.org/), [pandas](http://pandas.pydata.org/) and [statsmodels](http://statsmodels.sourceforge.net/).

Those libraries require to compile their code during the installation so it will take some time. But don't be scared, if you follow our instructions everything should be fine. Once they are installed it is very easy to get OncodriveFM ready to work.

We recommend to use [Anaconda](https://store.continuum.io/cshop/anaconda/), it is a Python distribution that includes numpy, scipy, pandas and statsmodels already compiled.

An alternative is to use [virtualenv](http://www.virtualenv.org/). virtualenv is a tool to create isolated *Python* environments. The basic problem being addressed is one of dependencies and versions, and indirectly permissions. With *virtualenv* you can install the libraries and programs without having to be *root* and without conflicting with other program's libraries.

If you are on *Mac OS X* or *Linux*, chances are that one of the following two commands will work for you:

	$ sudo easy_install virtualenv

or even better:

	$ sudo pip install virtualenv

One of these will probably install *virtualenv* on your system. Maybe it’s even in your package manager. If you use *Ubuntu*, try:

	$ sudo apt-get install python-virtualenv

If you are on *Windows* and don’t have the *easy_install* command, you must install it first. Check the *pip* and *distribute* on *Windows* section for more information about how to do that. Once you have it installed, run the same commands as above, but without the *sudo* prefix.

Once you have *virtualenv* installed, just fire up a shell and create your own environment.

	$ virtualenv env

Now, whenever you want to work on a project, you only have to activate the corresponding environment. On *OS X* and *Linux*, do the following:

	$ source env/bin/activate

If you are a *Windows* user, the following command is for you:

	$ env\scripts\activate

Either way, you should now be using your *virtualenv* (notice how the prompt of your shell has changed to show the active environment).

Now you can just enter the following commands to get the OncodriveFM dependencies installed in your *virtualenv*:

	(env) $ pip install -U distribute
	(env) $ pip install -U python-dateutil==2.1
	(env) $ pip install -U pytz==2013b
	(env) $ pip install -U numpy==1.7.1
	(env) $ pip install -U scipy==0.12.0
	(env) $ pip install -U pandas==0.12.0
	(env) $ pip install -U statsmodels==0.4.3

One problem that could arise is that scipy does not found the required libraries *BLAS* and *LAPACK* or *ATLAS*. In case they are not installed, you need to download and compile them by yourself. There is an installation guide at [http://www.scipy.org/Installing_SciPy](http://www.scipy.org/Installing_SciPy)

Then to get OncodriveFM installed run the following command:

	(env) $ pip install oncodrivefm

And that's all. The following command will allow you to check that is correctly installed by showing the command help:

	(env) $ oncodrivefm --help

	usage: oncodrivefm [-h] [-o PATH] [-n NAME] [--output-format FORMAT]
                       [-N NUMBER] [-e ESTIMATOR] [--gt THRESHOLD]
                       [--pt THRESHOLD] [-s SLICES] [-m PATH] [--save-data]
                       [--save-analysis] [-j CORES] [-D KEY=VALUE] [-L LEVEL]
                       DATA

    Compute the FM bias for genes and pathways

    positional arguments:
      DATA                  File containing the data matrix in TDM format

    optional arguments:
      -h, --help            show this help message and exit
      -o PATH, --output-path PATH
                            Directory where output files will be written
      -n NAME               Analysis name
      --output-format FORMAT
                            The FORMAT for the output file
      -N NUMBER, --samplings NUMBER
                            Number of samplings to compute the FM bias pvalue
      -e ESTIMATOR, --estimator ESTIMATOR
                            Test estimator for computation.
      --gt THRESHOLD, --gene-threshold THRESHOLD
                            Minimum number of mutations per gene to compute the FM
                            bias
      --pt THRESHOLD, --pathway-threshold THRESHOLD
                            Minimum number of mutations per pathway to compute the
                            FM bias
      -s SLICES, --slices SLICES
                            Slices to process separated by commas
      -m PATH, --mapping PATH
                            File with mappings between genes and pathways to be
                            analysed
      --save-data           The input data matrix will be saved
      --save-analysis       The analysis results will be saved
      -j CORES, --cores CORES
                            Number of cores to use for calculations. Default is 0
                            that means all the available cores
      -D KEY=VALUE          Define external parameters to be saved in the results
      -L LEVEL, --log-level LEVEL
                            Define log level: debug, info, warn, error, critical,
                            notset

## Running an example ##

There is an example included for CLL data. You can run the following command to see OncodriveFM in action:

	(env) $ oncodrivefm -e median -m data/ensg_kegg.tsv data/CLL.tdm

You will get this two files containing the results of the genes and pathways analysis:

### CLL-genes.tsv ###


	(env) $ head CLL-genes.tsv
	## version=0.3
	## date=2013-03-15 16:29:38
	## slices=SIFT,PPH2,MA
	## method=median-empirical
	ID	PVALUE	QVALUE
	ENSG00000162231	0.0635076442586	0.562415656261
	ENSG00000153820	0.0827513200276	0.59108085734
	ENSG00000196712	0.0731140353139	0.562415656261
	ENSG00000113494	0.949233244935	0.999876051041
	ENSG00000085224	0.128548472663	0.646323494199

### CLL-pathways.tsv ###

	(env) $ head CLL-pathways.tsv
	## version=0.3
	## date=2013-03-15 16:30:03
	## slices=SIFT,PPH2,MA
	## method=median-zscore
	ID	ZSCORE	PVALUE	QVALUE
    hsa04670	-3.1882205245	0.999284243417	0.999899409849
    hsa05168	2.02935990475	0.0212108229234	0.243924463619
    hsa05169	1.17197530328	0.120603485838	0.452113115061
    hsa05164	1.89814316485	0.0288386126709	0.265036832336
    hsa05166	1.45834147225	0.0723732221627	0.369907579943
