#!/usr/bin/env python
from __future__ import division

"""
Computes the sum of PMT values over the entire image.
"""

import dphil_paths

def main(**kwargs):
  datafiles = kwargs['datafiles']
  vdivide = kwargs['vdivide']

  cols = ["Source Filename", "Total PMT Value", "# Pixels", "Pixel PMT Density"]
  print '\t'.join(cols)

  for datafile in datafiles:
    statsvec = get_sum(datafile, vdivide=vdivide)

    for idx, stat in enumerate(statsvec):
      pixsum, npix = stat
      print "%s[%d]\t%f\t%d\t%f"%(datafile, idx, pixsum, npix, pixsum/npix)

def get_sum(datafile, vdivide=1):
  import numpy as np
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

  nrows, ncols = scandata.matrix.shape

  # note that this is an integer division, so will under-estimate
  # the number of rows needed by up to 1
  rowspersection = nrows // vdivide

  sectionstats = list()
  for secidx in xrange(vdivide):
    startrow = secidx * rowspersection

    # because of integer truncation in the calculation of rowspersection,
    # when we calculate the last section we need to take up any remainders
    # by going all the way to the bottom
    if secidx + 1 < vdivide:
      endrow = startrow + rowspersection
    else:
      endrow = nrows

    section = scandata.matrix[startrow:endrow,:]
    sectionstats.append((np.sum(section), section.size))

  return sectionstats

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the sum of PMT values over the entire image')
  parser.add_argument('-vdivide', type=int, default=1, help='Divides the image vertically the specified number of times, outputting a sum for each section. Defaults to 1, equal to summing the whole image as one section')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
