#!/usr/bin/env python
from __future__ import division
"""
Plots histogram of SIOS 2D scans
"""

import os.path as op

import numpy as np
import matplotlib.pyplot as plt

import matplotlib_setup

from utils import keypress

import dphil_paths

def main(**kwargs):
  datafile = kwargs.pop('datafile')
  vline = kwargs.pop('vline')
  pdf = kwargs.pop('pdf')

  import numpy as np
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()
  values = np.reshape(scandata.matrix, -1)

  plt.hist(values, bins=100, log=True, normed=True)

  if vline is not None:
    plt.vlines(vline, 0, 1, colors=['red'], linewidth=2)

  plt.xlabel('PMT Output (V)')
  plt.ylabel('Normalised Count')

  if pdf:
    from os.path import splitext, extsep
    pdfname = splitext(datafile)[0] + '__histo' + extsep + 'pdf'

    fig = plt.gcf()
    fig.savefig(pdfname, bbox_inches='tight')
    print 'PDF saved to', pdfname
  else:
    plt.show()


def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots histogram of intensity values in SIOS scans')
  parser.add_argument('datafile', type=str, help='WZ data file')
  parser.add_argument('-vline', type=float, help='Plots a vertical line at the specified X position')
  parser.add_argument('-pdf', action='store_true', help='If given saves a copy of the plot as PDF without displaying it')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
