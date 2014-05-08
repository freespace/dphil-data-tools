#!/usr/bin/env python
from os.path import basename

import numpy
import matplotlib.pyplot as plt

def _find_x(xvec, yvec, ytarget):
  """
  Returns a linearly interpolated x value where the function described by
  xvec and yvec
  """
  def interp(x1,y1,x2,y2):
    rise = y2-y1
    run = x2-x1
    grad = rise/run

    dy = ytarget - y1
    return x1+run*dy/rise

  start = None
  end = None
  for idx in xrange(len(yvec)-1):
    if start is None:
      if yvec[idx]<=ytarget and yvec[idx+1]>ytarget:
        start = interp(
            xvec[idx], yvec[idx],
            xvec[idx+1], yvec[idx+1])
    else:
      if yvec[idx]>=ytarget and yvec[idx+1]<ytarget:
        end = interp(
            xvec[idx], yvec[idx],
            xvec[idx+1], yvec[idx+1])

  if start is not None and end is not None:
    return end - start
  else:
    return None

def get_stats(xvec, yvec, noauc=False):
  """
  Returns the statistics for the given x and y vectors. If noauc is true, then
  None will be returned instead of the area under the curve.

  The statistics returned are, in order:

    - max
    - min
    - median
    - mean
    - standard deviation
    - area-under-curve [sum(y-y.median)]
    - FWHM, valid only if you know there is a single peak
  """

  stdev = numpy.std(yvec)
  mean = numpy.mean(yvec)
  median = numpy.median(yvec)
  peak = max(yvec)
  miny = min(yvec)
  auc = sum(yvec - median)

  start = None
  end = None

  ret = [peak, miny, median, mean, stdev, auc]


  m = median
  # Assume there is only one peak for now
  if peak > m+2*stdev:
    # half maximum is defined as 0.5*(peak+miny). Can't juse use 1/2 peak
    # as that doesn't take into account the noise floor
    hm = 0.5*(peak + miny)
    ret.append(_find_x(xvec, yvec, hm))

  else:
    ret += [None, None]
  return ret

def stats(**kwargs):
  csvfile = kwargs['csvfile']
  with open(csvfile) as csvhandle:
    header=['','# File: '+basename(csvfile)]
    done = False
    while not done:
      line = csvhandle.readline()
      if line[0] == '#':
        line = line.strip()
        line = line.replace('\t',' ')
        header.append(line)
      else:
        done = True

  try:
    mat = numpy.loadtxt(csvfile, delimiter='\t')
  except:
    mat = numpy.loadtxt(csvfile, delimiter=',')

  xvec = mat[:,0]

  def f(key):
    return kwargs[key] or kwargs['all']

  print csvfile
  print '\t\t\tMax (V)    \tMin (V)    \tMedian (V)\tMean (V)\tStdev (V)\tAUC (V)    \tFWHM (um)'
  print '\t','-'*121

  def p(yvec):
    s = get_stats(xvec, yvec)
    return '\t\t'.join(['%.2f'%(x) for x in s])

  if f('mon'):
    mon_vec = mat[:,2]
    print '\tMonitor\t\t', p(mon_vec)

  if f('bias'):
    bias_vec = mat[:,3]
    print '\tVbias\t\t', p(bias_vec)

  if f('ref'):
    ref_vec = mat[:,4]
    print '\tReflection\t', p(ref_vec)

  if f('pmt'):
    pmt_vec = mat[:,5]
    print '\tPMT\t\t', p(pmt_vec)

  if f('2'):
    _2_vec = mat[:,1]
    print '\t2\t\t', p(_2_vec)

  print ''

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Computes statistics for F410 scan data')
  parser.add_argument('-ref', action='store_true', help='Plot reflection')
  parser.add_argument('-mon', action='store_true', help='Plot monitor')
  parser.add_argument('-pmt', action='store_true', help='Plot PMT')
  parser.add_argument('-bias', action='store_true', help='Plot bias')
  parser.add_argument('-2', action='store_true', help='Plot the 2nd column')
  parser.add_argument('-all', action='store_true', help='Plot everything')

  parser.add_argument('csvfiles', nargs='+', type=str, help='CSV files to compute statistics for')

  args = vars(parser.parse_args())

  if filter(lambda x:args[x], ['ref', 'mon', 'pmt', 'bias', '2']) == []:
    args['all'] = True

  for csvfile in args['csvfiles']:
    args['csvfile'] = csvfile
    stats(**args)
