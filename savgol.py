#!/usr/bin/env python

"""
This script implements Savitzky-Golay filtering on 1D
scan data
"""

import numpy as np
from scipy.signal import savgol_filter

import dphil_paths

def filter_one(npzfile, yindex, windowsize, order):
  from dataloader import DataLoader
  data = DataLoader(npzfile)

  mat = data.matrix
  xvec = mat[:,0]
  yvec = mat[:,yindex]

  filteredyvec = savgol_filter(yvec, windowsize, order)

  mat = np.column_stack((xvec, filteredyvec))

  from os.path import basename, splitext
  fname = splitext(basename(npzfile))[0]
  outnpz = fname + '_savgol.npz'
  header = {'source_file':npzfile,
            'window_size':windowsize,
            'order':order}

  np.savez(outnpz, data=mat, source='savgol.py', header=header)
  print 'Saved filtered data to', outnpz

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Performs Savitzky-Golay filtering')

  parser.add_argument('-yindex', default=1, type=int, help='Index of Y series data to compute stats for. Defaults to all Y series data.')
  parser.add_argument('-windowsize', default=31, type=int, help='Window size to use, default 31')
  parser.add_argument('-order', default=2, type=int, help='Order to use, default 2')
  parser.add_argument('npzfiles', nargs='+', type=str, help='NPZ files to filter')

  args = vars(parser.parse_args())

  for npzfile in args['npzfiles']:
    filter_one(npzfile, args['yindex'], args['windowsize'], args['order'])
