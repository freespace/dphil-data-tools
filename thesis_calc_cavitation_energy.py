#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

def p(s):
  import sys
  sys.stderr.write(s)

def pln(s):
  p(s)
  p('\n')

def main(power_file=None, binsize=5, max_bins=601, head_skip=0):
  npz = np.load(power_file)
  filenamelist = npz.keys()
  pln('\t%d merged files'%(len(filenamelist)))
  pln('\t%d will be skipped'%(head_skip))

  filenamelist.sort()

  energy = 0
  starttime = None
  endtime = None
  for fdx, fname in enumerate(filenamelist[head_skip:]):
    datadict = npz[fname].item()
    data = datadict['data']
    powervec = data[:,1]
    energy += sum(powervec)

    header = datadict['header']
    trigtimestr = header['trigtime']
    from datetime import datetime
    # really should standardise on a datetime format, e.g. ISO 8601. However
    # python is unlikely to change how str(datetime) works so this is probably
    # ok for now.
    trigtime = datetime.strptime(trigtimestr, '%Y-%m-%d %H:%M:%S.%f')
    if starttime is None:
      starttime = trigtime

    endtime = trigtime

    # binning makes no difference to the actual values, we need it
    # to know how many traces should we be integrating over
    if fdx >= binsize * max_bins:
      break

    if (fdx+1)%10 == 0:
      p('.')

  pln('')
  duration = endtime - starttime
  duration = duration.total_seconds()
  pln('\tDuration:%.2f'%(duration))
  pln('\t\t%s ---> %s'%(starttime, endtime))

  traces_per_second = len(filenamelist)/duration
  pln('\tTraces per second %f'%(traces_per_second))

  # need to divide by the number of traces per seconds as sometimes
  # I capture 5/sec and sometime 1/s or 2.2/s. If I don't do this then
  # the 5/sec data will naturally have more 'energy'
  print energy / traces_per_second, '\t', duration, '\t', traces_per_second

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Integrates power spectrum over time to measure the total detected cavitation energy')
  parser.add_argument('-head_skip', type=int, default=0, help='Number of files to skip before head of the queue. Files will be sorted before skip is applied. Negative values are allowed, in which case it turns into tail skip')
  parser.add_argument('-binsize', type=int, default=5, help='Perform binning with the given bin size. Bin size does not have to be a integer divisor of the number of samples')
  parser.add_argument('-max_bins', type=int, default=601, help='Plot no more than this number of bins')
  parser.add_argument('power_file', type=str, help='Merged npz output produced by calc_power_spectrum.py')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
