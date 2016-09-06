#!/usr/bin/env python

from __future__ import division
import numpy as np
import matplotlib.pyplot as plt

import matplotlib_setup

import dphil_paths

def get_npz(scan_id, scan_number):
  import os
  # get files ending in NPZ
  npzfilenames = filter(lambda x:x.endswith('.npz'), filter(os.path.isfile, os.listdir('.')))

  # match on scan_id
  npzfilenames = filter(lambda x: scan_id in x, npzfilenames)

  # match on scan_number
  for fname in npzfilenames:
    if int(fname.split('-')[1]) == scan_number:
      return fname

  return None

def main(**kwargs):
  scanID = kwargs.pop('scanID')
  pdf = kwargs.pop('pdf')
  png = kwargs.pop('png')
  save_suffix = kwargs.pop('save_suffix')
  PMT_coeff = kwargs.pop('PMT_coeff')

  def get_matrix(obj):
    return obj.matrix * PMT_coeff

  from dataloader import DataLoader
  nrows = 2
  ncols = 3

  DOX_30uM_V = 1.5
  DOX_50uM_V = 2.4

  scan_interval_min = 2

  plt.figure(figsize=(16,8))

  for curplot in xrange(nrows*ncols):
    plt.subplot(nrows, ncols, curplot+1)
    scannumber = curplot*15
    scanfile = get_npz(scanID, scannumber)
    if scanfile:
      loader = DataLoader(scanfile)
      scandata = loader.source_obj
      scandata = loader.source_obj
      plt.contour(scandata.zpositionvec/1000,
            scandata.wpositionvec/1000,
            get_matrix(scandata),
            levels=[DOX_30uM_V, DOX_50uM_V],
            colors=['g', 'b'])
      plt.xlabel('Z Position (mm)')
      plt.ylabel('X Position (mm)')
      plt.title('$t=%d$ min'%(scannumber*scan_interval_min))

  plt.tight_layout()

  # OK so it is obvious that diffusion happens. Now to characterise how much. We will do this by scanning left-to-right and look for when the fluorescence value exceeds 2.4 V, which is 50 uM. We will do this for the first and last image, and the difference in Z position is the movement of the 50 uM concentration "front".

  # In[69]:

  plt.figure(figsize=(16,9))
  plt.hold(True)

  wavefront_z_proximal_dict = dict()

  threshold_V = DOX_30uM_V
  threshold_n = 3

  scanidx_shortlist = [0, 15, 30, 45, 60]

  for scanidx in scanidx_shortlist:
    scanfile = get_npz(scanID, scanidx)
    assert scanfile is not None, 'Failed to find scan %03d for scan with ID %s'%(scanidx, scanID)

    loader = DataLoader(scanfile)
    scandata = loader.source_obj
    mat = get_matrix(scandata)
    wavefront_z_proximal_vec = list()
    for rowidx in xrange(mat.shape[0]):
      row = mat[rowidx, :]
      # wtf? where returns a tuple containing an array containing indices...
      z_idx_vec = np.where(row>threshold_V)[0]
      # we don't want the first pixel that is larger than threshold as otherwise
      # the data will be very noisy. Instead we require the threshold to have
      # been crossed n times
      n = min(threshold_n, len(z_idx_vec)-1)
      z_idx = z_idx_vec[n]

      z_pos = scandata.zpositionvec[z_idx]
      wavefront_z_proximal_vec.append(z_pos)

    wavefront_z_proximal_dict[scanidx] = wavefront_z_proximal_vec
    t=scanidx*scan_interval_min
    plt.plot(scandata.wpositionvec, wavefront_z_proximal_vec, label='t=%d min'%(t))

  plt.legend(loc='best')
  plt.xlabel('X Position (um)')
  plt.ylabel('30 uM DOX Contour Distance From Objective (um)')
  plt.grid(axis='y')


  # As expected over time the wavefront has moved towards the objective, i.e. away from the channel. but by how much?

  # In[70]:

  plt.figure(figsize=(16,9))

  # 2 tuple of (mean, stdev)
  wavefront_z_diff_vec = list()
  for lastscanidx, curscanidx in zip(scanidx_shortlist[:-1], scanidx_shortlist[1:]):
    wavefront_z_proximal_current = np.asarray(wavefront_z_proximal_dict[curscanidx])
    wavefront_z_proximal_last = np.asarray(wavefront_z_proximal_dict[lastscanidx])
    wavefront_z_proximal_diff = wavefront_z_proximal_last - wavefront_z_proximal_current

    movement_mean = np.mean(wavefront_z_proximal_diff)
    movement_stdev = np.std(wavefront_z_proximal_diff)
    wavefront_z_diff_vec.append((movement_mean, movement_stdev))

  xvec = np.arange(len(scanidx_shortlist)-1)
  meanvec = map(lambda x:x[0], wavefront_z_diff_vec)
  stdvec = map(lambda x:x[1], wavefront_z_diff_vec)
  plt.bar(xvec+0.1, meanvec, yerr=stdvec, color='0.75', edgecolor='k', ecolor='k', width=0.8)

  tickvec = map(lambda x:'$t=%d$ min'%(x*scan_interval_min), scanidx_shortlist[1:])

  plt.xticks(xvec+0.5, tickvec)
  plt.xlabel('Elapsed Time (min)')
  tinterval = (scanidx_shortlist[1]-scanidx_shortlist[0])*scan_interval_min
  plt.ylabel('30 uM Contour Movement Over %d Minutes (um)'%(tinterval))
  ymax = plt.ylim()[1]
  plt.ylim([0, ymax])
  plt.grid(axis='y')

  # Lets see how this varies across the channel by plotting the movement along
  # the channel between the first and last scan

  plt.figure(figsize=(16,9))
  plt.hold(True);

  movement_mean = -1
  movement_stdev = -1

  wavefront_z_proximal_first = np.asarray(wavefront_z_proximal_dict[0])

  for curscanidx in scanidx_shortlist[1:]:
    wavefront_z_proximal_current = np.asarray(wavefront_z_proximal_dict[curscanidx])
    wavefront_z_proximal_diff = wavefront_z_proximal_first - wavefront_z_proximal_current

    movement_mean = np.mean(wavefront_z_proximal_diff)
    movement_stdev = np.std(wavefront_z_proximal_diff)

    lbl = '$t=%d$ min'%(curscanidx*scan_interval_min)
    plt.plot(scandata.wpositionvec, wavefront_z_proximal_diff, label=lbl)

  plt.xlabel('X Position (um)')
  plt.ylabel('Total 30 uM Contour Movement (um)')
  lastt = scanidx_shortlist[-1]*scan_interval_min
  plt.title('$t=%d$ min  mean=%.2f um SD=%.2f'%(lastt, movement_mean, movement_stdev))

  plt.grid(axis='y')
  plt.legend()
  # We can also visualise it another way by looking at the line profile at top, middle and bottom of the first and last scan.

  # In[71]:

  plt.figure(figsize=(16,7))
  plotidx = 1
  for scanidx in [0, 60]:
    scanfile = get_npz(scanID, scanidx)
    loader = DataLoader(scanfile)
    scandata = loader.source_obj
    mat = get_matrix(scandata)

    zposvec = scandata.zpositionvec/1000
    xposvec = scandata.xpositionvec/1000

    nrows = mat.shape[0]
    subplotrows = 2
    subplotcols = 3
    for rowidx in [0, nrows//2, nrows-1]:
      plt.subplot(subplotrows, subplotcols, plotidx)
      row = mat[rowidx, :]
      plt.plot(zposvec, row)
      plt.title('$t=%d$ min $x=%.2f$ mm'%(scanidx*scan_interval_min, xposvec[rowidx]))
      plotidx += 1
      plt.xlabel('Z Position (mm)')
      plt.ylabel('PMT Output (V)')

      wavefront_z = wavefront_z_proximal_dict[scanidx][rowidx]/1000
      plt.vlines(wavefront_z, 0, 20, color='r', linewidth=2)

  plt.tight_layout()

  print 'Done plotting'

  if pdf or png:
    for fignum in plt.get_fignums():
      if plt.fignum_exists(fignum):
        fig = plt.figure(num=fignum)
        if len(save_suffix) and save_suffix[0] != '_':
          save_suffix = '_'+save_suffix
        savename = scanID + '_fig%s'%(str(fignum)) + save_suffix

        def s(ext):
          from os.path import extsep
          dstname = savename + extsep + ext
          fig.savefig(dstname, bbox_inches='tight')
          print 'Saved figure to', dstname

        if pdf:
          s('pdf')
        if png:
          s('png')
  else:
    plt.show()

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the sum of PMT values over the entire image')
  parser.add_argument('scanID', type=str, help='Scan ID of scan to produce plots for')
  parser.add_argument('-pdf', action='store_true', help='If given saves a copy of the plot as PDF without displaying it')
  parser.add_argument('-png', action='store_true', help='If given saves a copy of the plot as PNG without displaying it')
  parser.add_argument('-PMT_coeff', type=float, default=1, help='Multiplies all PMT voltages by the specified coefficient')
  parser.add_argument('-save_suffix', type=str, default='', help='If given will be inserted just before .pdf or .png with a leading _')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
