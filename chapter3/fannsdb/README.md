# FannsDb

This is the core library needed to work with the fannsdb database. It also contains a flexible parser for mutations
that allows them to be specified in both genomic and protein coordinates.

For protocols please look at the IPython Notebooks under the *notebooks* folder:

* **fannsdb-create-online-05.ipynb**: The steps required to create the database that require internet access. I used sydney to host the notebook.
* **fannsdb-create-offline-05.ipynb**: The steps required to create the database that don’t require internet access. I used the nodes 1 to 10 of the genecluster. It can be easily adapted to use any other workstation by changing the IPython.parallel client profile name and the configuration cell with the new paths.
* **fannsdb-datasets.ipynb**: This is a very important notebook with the steps required to create all the proxy datasets used in performance evaluation in FannsDB benchmarking and TransFIC evaluation.
* **fannsdb-perf.ipynb**: The steps required to calculate the performance metrics and figures. I used gencluster to host this notebook, but as the previos notebook can be easily adapted to be used in any workstation.
