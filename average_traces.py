#!/usr/bin/env python
"""
This script reads in time-value traces and outputs the averaged trace to a npz file
"""

from __future__ import division

import numpy as np

import dphil_paths

def main(**kwargs):
  npzfilevec = kwargs['npzfiles']

  yvec_sum = None
  xvec0 = None

  print 'Averaging traces %s ... %s'%(npzfilevec[0], npzfilevec[-1])

  for npzfile in npzfilevec:
    with np.load(npzfile) as npzfile:
      mat = npzfile['data']
      xvec = mat[:,0]
      yvec = mat[:,1]

      if 'source' in npzfile:
        source = npzfile['source'].item()
        assert not source == 'average_traces.py'

      if xvec0 is None:
        xvec0 = xvec

      assert len(xvec0) == len(xvec)

      if yvec_sum is None:
        yvec_sum = yvec
      else:
        yvec_sum += yvec

      import sys
      sys.stdout.write('.')
  print('')

  avg_yvec = yvec_sum / len(npzfilevec)

  outmat = np.column_stack((xvec0, avg_yvec))

  outputfile = '%s__%s.average.npz'%(npzfilevec[0], npzfilevec[-1])
  np.savez(outputfile, data=outmat, header=dict(inputs=npzfilevec), source='average_traces.py')
  print('Wrote average trace to %s'%(outputfile))


def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the average time-value trace from inputs')
  parser.add_argument('npzfiles', nargs='+', help='NPZ files to load traces from')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
