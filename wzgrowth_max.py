#!/usr/bin/env python
from __future__ import division

"""
This script tracks the growth of any deformation in XZ scans.

It works by sectioning the image into 3 horizontal sections in ratio of 1:2:1.
Then in each section it determines when smallest z value in which the section
maximum occurs.

The value recorded for each section is then *substracted* from the Z position
of first scan. The result is then a measure of the difference between the first
scan and the current scan. Because lower Z is to the left and US is also to the
left the result is conveniently positive.

Furthermore growth data of section 2, the central section, is detrended
against section 1 by subtracting from it section 1's growth value.

The result then is 3 sets of Z-position-over-time which is then written
to disk as NPZ along with the reference value used. The save data
is a matrix in the form:

  [t_0, sec1_growth, ... , sec3_growth, sec2_detrend]
  ...
  [t_n, sec1_growth, ... , sec3_growth, sec2_detrend]

Rationale for tracking the maximum is that any other value will be affected by
diffusion AND deformation, while the maximum is only affected by deformation as
it will shift the fluorescent peak.

The value measured will *not* be a measure of the size of the deformation, as
the fluorescent peak's movement will not be as extreme as the movement of the
deformation.
"""

import numpy as np

import dphil_paths

def p(s,newline=True):
  import sys
  sys.stderr.write(s)

  if newline:
    sys.stderr.write('\n')

def get_npz(scan_id, scan_number):
  import os
  # get files ending in NPZ
  npzfilenames = filter(lambda x:x.endswith('.npz'), filter(os.path.isfile, os.listdir('.')))

  # match on scan_id
  npzfilenames = filter(lambda x: scan_id in x, npzfilenames)

  # match on scan_number
  for fname in npzfilenames:
    if '-' in fname:
      if int(fname.split('-')[1]) == scan_number:
        return fname

  return None

def compute_growth(npz, debug):
  from dataloader import DataLoader
  loader = DataLoader(npz)
  scandata = loader.source_obj

  nrows, ncols = scandata.matrix.shape

  # we deal with the 1:2:1 ratio by dividing into 4 and merging
  # the center 2
  sec_ratio = (1,2,1)
  nsubsections = sum(sec_ratio)
  nsections = 3

  # note that this is an integer division, so will under-estimate
  # the number of rows needed by up to 1
  rows_per_subsection = nrows // nsubsections

  min_z_vec = list()
  min_rdx_vec = list()

  sec_boundary_vec = list()

  startrow = 0
  for secidx, rowspan in zip(xrange(nsections), sec_ratio):
    # because of integer truncation in the calculation of rowspersection,
    # when we calculate the last section we need to take up any remainders
    # by going all the way to the bottom
    if secidx + 1 < nsections:
      endrow = startrow + rows_per_subsection * rowspan
    else:
      endrow = nrows

    section = scandata.matrix[startrow:endrow,:]
    sec_boundary_vec.append((startrow, endrow))

    # print section.shape
    # update startrow for the next loop.
    startrow = endrow + 1

    p('.', False)

    min_rdx = None

    while min_rdx is None:
      for row in section:
        exceed_cnt = 0
        for rdx, val in enumerate(row):
          if val >= section.max()*0.95:
            if min_rdx is None or rdx < min_rdx:
              min_rdx = rdx
            break

    assert min_rdx is not None

    min_z = scandata.zpositionvec[min_rdx]
    min_z_vec.append(min_z)

    min_rdx_vec.append(min_rdx)

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress

    # hilight the section boundary
    # and the recorded Z location
    mat = scandata.matrix
    for secidx in xrange(nsections):
      startrow, endrow = sec_boundary_vec[secidx]

      mat[startrow] = np.ones(mat.shape[1])*mat.max()

      mat[startrow:endrow,min_rdx_vec[secidx]] = np.ones(endrow-startrow) * mat.max()

    plt.imshow(mat, interpolation='None', cmap='gnuplot2')
    plt.colorbar()
    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

  from wzmeta import get_meta
  meta = get_meta(None, scandata=scandata, time_as_string=False)

  t = meta['starttime']
  ret = [t] + min_z_vec
  return np.asarray(ret)

def main(scan_id=None, debug=False):
  # keep reading scans until we run out
  scan_num = 0
  done = False

  row_vec = list()

  while not done:
    npz = get_npz(scan_id, scan_num)
    scan_num += 1

    if npz is None:
      done = True
      break
    p('%d'%(scan_num), False)
    row_vec.append(compute_growth(npz, debug))

  p('done')

  # compute the growth distance
  # if we don't do this we end up modifying row0
  row0 = np.copy(row_vec[0])
  for row in row_vec:
    row[1:] = row0[1:] - row[1:]
    # compute relative time
    row[0] = row[0] - row0[0]

  growth_matrix = np.vstack(row_vec)

  # detrend central section
  detrended = growth_matrix[:,2] - growth_matrix[:,1]
  # make it into a column vector
  detrended = detrended.reshape(detrended.size, 1)

  growth_matrix = np.hstack((growth_matrix, detrended))

  p('Matrix shape %s'%(str(growth_matrix.shape)))

  savedata = dict(growth_matrix=growth_matrix,
                  source='wzgrowth.py',
                  scan_id=scan_id)

  outputfile = scan_id + '_growth_max.npz'
  np.savez_compressed(outputfile, **savedata)
  p('Growth data saved to %s'%(outputfile))

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Measures growth of deformation over time in XZ scans')
  parser.add_argument('-debug', action='store_true', help='If given the sections boundaries will be shown for each image.')
  parser.add_argument('scan_id', type=str, help='Scan ID of scan to measure')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
