#!/usr/bin/env python
from __future__ import division

"""
This script tracks the growth of any deformation in XZ scans.

It works by sectioning the image into 3 section, with the section
at lowest X starting position, the inlet of the channel, serving as
the reference. The first section will be called the reference section.

The half-maximum of the reference section is computed, and then for
each of ections the position at which the recorded value
exceeds the half-maximum for the 3rd time is recorded, and the smallest
Z position taken to be the metric for the section at the sampling time.

The computed Z position is *subtracted* from the Z position of the first scan.
The result is then a measure of the difference between the first scan and the
current scan. Because lower Z is to the left and US is also to the left the
result is conveniently positive.


The result then is 3 sets of Z-position-over-time which is then written
to disk as NPZ along with the reference value used. The save data
is a matrix in the form:

  [t0, ref_value, section_1_z, section_2_z, section_3_z]
  ...
  [t_last, ref_value, section_1_z, section_2_z, section_3_z]

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

  nsections = 3
  # note that this is an integer division, so will under-estimate
  # the number of rows needed by up to 1
  rowspersection = nrows // nsections

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress
    mat = scandata.matrix
    for secidx in xrange(nsections):
      mat[secidx*rowspersection] = np.ones(mat.shape[1])*mat.max()

    plt.imshow(mat)
    plt.gcf().canvas.mpl_connect('key_press_event', keypress)
    plt.show()
    plt.close()

  half_max = None
  min_z_vec = list()

  for secidx in xrange(nsections):
    startrow = secidx * rowspersection

    # because of integer truncation in the calculation of rowspersection,
    # when we calculate the last section we need to take up any remainders
    # by going all the way to the bottom
    if secidx + 1 < nsections:
      endrow = startrow + rowspersection
    else:
      endrow = nrows

    section = scandata.matrix[startrow:endrow,:]

    min_rdx = None
    if secidx == 0:
      # this is the reference section, so compute the half-maximum
      half_max = np.amax(section)/2

    for row in section:
      exceed_cnt = 0
      for rdx, val in enumerate(row):
        if val > half_max:
          exceed_cnt += 1

        if exceed_cnt >= 3:
          if min_rdx is None or rdx < min_rdx:
            min_rdx = rdx
          break

    min_z = scandata.zpositionvec[min_rdx]
    min_z_vec.append(min_z)

  from wzmeta import get_meta
  meta = get_meta(None, scandata=scandata, time_as_string=False)

  t = meta['starttime']
  ret = [t, half_max] + min_z_vec
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
    p('%d..'%(scan_num), False)
    row_vec.append(compute_growth(npz, debug))

  # compute the growth distance
  # if we don't do this we end up modifying row0!
  row0 = np.copy(row_vec[0])
  for row in row_vec:
    row[2:] = row0[2:] - row[2:]

  growth_matrix = np.vstack(row_vec)
  p('done')
  p('Matrix shape %s'%(str(growth_matrix.shape)))

  if not debug:
    savedata = dict(growth_matrix=growth_matrix,
                    source='wzgrowth.py',
                    scan_id=scan_id)

    outputfile = scan_id + '_growth.npz'
    np.savez_compressed(outputfile, **savedata)
    p('Growth data saved to %s'%(outputfile))

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Measures growth of deformation over time in XZ scans')
  parser.add_argument('-debug', action='store_true', help='If given the sections boundaries will be shown for each image. No data is saved.')
  parser.add_argument('scan_id', type=str, help='Scan ID of scan to measure')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
