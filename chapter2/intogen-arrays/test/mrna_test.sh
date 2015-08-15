#!/bin/bash

wok-run.py -c portege.conf -c ../conf/common.conf -c ../src/mrna/mrna.conf -c mrna_test.conf -c ../conf/debug.conf ../src/mrna/mrna_test.flow
