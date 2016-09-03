#!/usr/bin/env python
from __future__ import division

"""
Computes the nth percentile of a SIOS scan
"""

import dphil_paths

def main(**kwargs):
  datafiles = kwargs.pop('datafiles')
  percentile = kwargs.pop('percentile')

  cols = ["Source Filename", "%.2fth Percentile"%(percentile), "Pixels at or above"]

  print '\t'.join(cols)

  for fileidx, datafile in enumerate(datafiles):
    import numpy as np
    npzfile = np.load(datafile)
    scandata = npzfile['scandata'].item()
    res = np.percentile(scandata.matrix, percentile)
    cnt = np.count_nonzero(scandata.matrix > res)
    print '\t'.join(map(str,[datafile, res, cnt]))

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes nth  percentile values over an scan')
  parser.add_argument('percentile', type=float, help='The nth percentile to find')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
