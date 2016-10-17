#!/usr/bin/env python
from __future__ import division

"""
This script is a modified version of wzgrowth.py that finds the fluorescence
front for each row instead of each section.

It will only produce plots, not data
"""

import numpy as np

import dphil_paths
from debug_print import p, pln

def load_scandata_with_correction(npzfilename):
  from dataloader import DataLoader
  loader = DataLoader(npzfilename)
  scandata = loader.source_obj

  assert scandata.axial_scaling_correction_applied, 'Your version of ScanData is too old!'

  return scandata

def get_npz(scan_id, scan_number):
  import os
  # get files ending in NPZ
  npzfilenames = filter(lambda x:x.endswith('.npz'), filter(os.path.isfile, os.listdir('.')))

  # match on scan_id
  npzfilenames = filter(lambda x: scan_id in x, npzfilenames)

  # match on scan_number
  for fname in npzfilenames:
    if '-' in fname:
      parts = fname.split('-')
      if len(parts) >= 4:
        try:
          if int(parts[1]) == scan_number:
            return fname
        except:
          pass

  return None

def estimate_threshold(scan_id, channel_width_um):
  npz = get_npz(scan_id, 0)
  scandata = load_scandata_with_correction(npz)
  ref_sec = scandata.matrix[0:25,:]

  threshold = ref_sec.max() * 0.5
  rdx_sum = 0
  exceed_cnt = 0
  for row in ref_sec:
    # forward scan to find first crossing
    for rdx, val in enumerate(row):
      if val > threshold:
        rdx_sum += rdx
        exceed_cnt += 1
        break

    # backward scan to find last crossing
    for rdx, val in enumerate(reversed(row)):
      if val > threshold:
        # get the fwd index, remember that the
        # row values are reversed
        rdx = row.size - rdx - 1

        rdx_sum += rdx

        # no need to increment exceed_cnt since the
        # forward scan done it already
        break

  rdx_centre = rdx_sum / 2 / exceed_cnt
  zstep_um = scandata.zpositionvec[1] - scandata.zpositionvec[0]
  channel_width_idx = channel_width_um / zstep_um
  rdx_thres = rdx_centre - channel_width_idx // 2

  print 'Channel centre at', rdx_centre * zstep_um + scandata.zpositionvec[0]
  print 'Proximal channel wall at', rdx_thres * zstep_um + scandata.zpositionvec[0]
  print 'Point sampled value',ref_sec[0][rdx_thres]
  print '\t',ref_sec[0][rdx_thres-1:rdx_thres+2]
  thres_sum = 0
  for row in ref_sec:
    thres_sum += row[rdx_thres]
  return thres_sum / ref_sec.shape[0]

def find_min_rdx(row, threshold):
    # basic protection against 'hot' pixels. The mechanism
    # employed here allows us to detect a crossings with 1
    # event even when we want 2 ideally
    exceed_threshold = 2

    # find the proximal edge of the channel boundary
    crossings = list()
    rdx_vec = list()
    for rdx, val in enumerate(row):
      if val >= threshold:
        crossings.append(rdx)

      if len(crossings) >= exceed_threshold:
        break

    if len(crossings):
      #if secidx == 0:
      #  print zdx_to_pos(crossings[-1]), val
      rdx_vec.append(crossings[-1])

    if len(rdx_vec) > 0:
      rdx_vec = np.asarray(rdx_vec)
      min_rdx = rdx_vec.min()
      assert min_rdx is not None
      return min_rdx
    else:
      return None

def compute_growth(npz, threshold, **kwargs):
  scandata = load_scandata_with_correction(npz)
  nrows, ncols = scandata.matrix.shape

  min_z_vec = list()
  min_rdx_vec = list()

  def zdx_to_pos(zdx):
    zstart = scandata.zpositionvec[0]
    zstep_um = scandata.zpositionvec[1] - zstart
    return zdx * zstep_um + zstart

  for row in scandata.matrix:
    p('.')
    min_rdx = find_min_rdx(row, threshold)
    if min_rdx is None:
      min_rdx = find_min_rdx(row, threshold=row.max()*0.5)
      p('o')

    min_z = scandata.zpositionvec[min_rdx]
    min_z_vec.append(min_z)

    min_rdx_vec.append(min_rdx)

  import matplotlib.pyplot as plt
  import matplotlib_setup
  from utils import keypress

  def plot_mat(mat, saveto, cmap='jet', colorbar=True):
    extent = [scandata.zpositionvec.min(), scandata.zpositionvec.max()]
    extent += [scandata.wpositionvec.max(), scandata.wpositionvec.min()]
    plt.imshow(mat, interpolation='None', extent=extent, cmap=cmap, origin='upper')
    plt.xlabel('Z Position (um)')
    plt.ylabel('X Position (um)')
    if colorbar:
      plt.colorbar()
    plt.gcf().savefig(saveto, format='pdf', bbox_inches='tight')
    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

  # hilight the section boundary
  # and the recorded Z location
  mat = scandata.matrix

  plot_mat(mat, npz+'-orig.pdf')

  for rdx in xrange(mat.shape[0]):
    mat[rdx] = np.zeros(row.shape)
    mat[rdx][min_rdx_vec[rdx]] = 1
    mat[rdx][min_rdx_vec[rdx]-1] = 1

  plot_mat(mat, npz+'-contour.pdf', cmap='Greys', colorbar=False)

  from wzmeta import get_meta
  meta = get_meta(None, scandata=scandata, time_as_string=False)

  t = meta['starttime']
  ret = [t] + min_z_vec + [threshold]
  return np.asarray(ret)

def main(scan_id=None, scan_num=0, suffix='', channel_width_um=None, **kwargs):
  # keep reading scans until we run out
  done = False

  row_vec = list()

  threshold = estimate_threshold(scan_id, channel_width_um)

  p('Threshold=%.2f'%(threshold))

  npz = get_npz(scan_id, scan_num)
  scan_num += 1

  p('%d'%(scan_num), False)
  row_vec.append(compute_growth(npz, threshold, **kwargs))

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Measures growth of deformation over time in XZ scans')
  parser.add_argument('-suffix', type=str, default='', help='If given will be appeneded to output filename')
  parser.add_argument('-channel_width_um', type=float, default=370, help='Specifies the width of the channel to use when deriving reference fluorescence value. Ignored if -threshold is given. Default: 370 um')
  parser.add_argument('-ignore_bad_rows', action='store_true', default=False, help='Disables bad row detection, useful when I have an image at 100 um not 50 um steps')
  parser.add_argument('-ignore_outliers', action='store_true', default=False, help='Disables outlier detection')
  parser.add_argument('scan_id', type=str, help='Scan ID of scan to measure')
  parser.add_argument('scan_num', type=int, help='Scan number of scan to measure')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
