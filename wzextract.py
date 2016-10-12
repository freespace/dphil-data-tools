#!/usr/bin/env python
"""
This script extracts individual Z scans from a WZ scan file. Note that as of
2016-10-10 the output Z positions will be corrected for refractive index mismatch
"""

from __future__ import division

import numpy as np

import dphil_paths
def _get_filename(wzfile, zindex, transpose, debug):
  import os.path as op
  fname = op.basename(wzfile)
  fname = op.splitext(fname)[0]
  fname += '__%d'%(zindex)

  if transpose:
    fname += '-W'

  if debug:
    fname += '-debug'

  fname += op.extsep + 'npz'
  return fname

def main(**kwargs):
  datafiles = kwargs['datafiles']
  zindex = kwargs['index']
  transpose = kwargs['transpose']
  debug = kwargs['debug']

  assert zindex >= 0, 'index cannot be negative'
  for wzfile in datafiles:
    npzfile = np.load(wzfile)
    scandata = npzfile['scandata'].item()
    fname = _get_filename(wzfile, zindex, transpose, debug)

    if transpose:
      mat = scandata.matrix.T
      axis = 'W'
    else:
      axis = 'Z'
      mat = scandata.matrix

    nrows = mat.shape[0]
    assert zindex < nrows, 'Row %d requested when only %d rows available'%(zindex, nrows)

    zvec = mat[zindex,:]

    if debug:
      import matplotlib.pyplot as plt
      import matplotlib_setup
      from utils import keypress
      # set the selected index to the maximum value so when plotted it saturates
      mat[zindex,:] = np.full(zvec.shape, mat.max())
      extent = [scandata.zpositionvec.min(), scandata.zpositionvec.max()]
      extent += [scandata.wpositionvec.min(), scandata.wpositionvec.max()]

      plt.imshow(mat, interpolation='None', extent=extent, cmap='gray')
      plt.colorbar()
      plt.gcf().canvas.mpl_connect('key_press_event', keypress)
      plt.xlabel('Z Position (um)')
      plt.ylabel('X Position (um)')

      plt.show()
      plt.close()
    else:
      if transpose:
        zposvec = scandata.wpositionvec
      else:
        zposvec = scandata.zpositionvec

      zmat = np.column_stack((zposvec, zvec))

      from wzmeta import get_meta
      np.savez(fname, data=zmat, header=get_meta(wzfile), source='wzextract.py')

      print 'Saved %s scan index %d to %s'%(axis, zindex, fname)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Extracts a specific Z scan from WZScan files')

  parser.add_argument('-transpose',
                      action='store_true',
                      help="""If given the scan will be transposed before
                      extracting. This allows slices through the non-Z
                      dimension.""")

  parser.add_argument('-debug',
                      action='store_true',
                      help="""If given the output will be a copy of the input,
                              but with the selected Z scan set to the maximum
                              value. This is useful for visually verifying that
                              specified z-scan is in the right place""")

  parser.add_argument('index', type=int, help='Index of the Z scan to extract')

  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
