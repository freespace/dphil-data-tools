#!/usr/bin/env python
from os.path import basename

import numpy
from scipy import stats as STATS
import matplotlib.pyplot as plt

from csvtools import CSVReader

def find_width(xvec, yvec, ytarget):
  """
  Finds distance between 2 points on a curve described by xvec and yvec
  where yvec is greater than ytarget.

  The distance is defined as the distance between the left most point above
  ytarget and the right most point above ytarget.
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
    if yvec[idx]<=ytarget and yvec[idx+1]>ytarget:
      start = interp(
          xvec[idx], yvec[idx],
          xvec[idx+1], yvec[idx+1])
      break

  for idx in xrange(len(yvec)-1,-1, -1): 
    if yvec[idx]<=ytarget and yvec[idx-1]>ytarget:
      end = interp(
          xvec[idx], yvec[idx],
          xvec[idx-1], yvec[idx-1])
      break

  if start is not None and end is not None:
    # take the abs value because sometimes our z values
    # are in descending order because a scan is taken
    # backwards
    return abs(end - start)
  else:
    return None

def get_stats(xvec, yvec, noauc=False, asdict=False):
  """
  Returns the statistics for the given x and y vectors. If noauc is true, then
  None will be returned instead of the area under the curve.

  If asdict is True, then instead of a list a dictionary will be returned
  with keys as indicated below, e.g. max, min, FWHM.

  The statistics returned are, in order:

    - max
    - min
    - median
    - mean
    - stdev (standard deviation)
    - area-under-curve (=sum(y-y.mode))
    - FWHM, valid only if you know there is a single peak, and the mode
      correspods to the noise floor.
    - mode used to calculate FWHM

  FWHM is calculated by finding the "half maximum" as 0.5*(peak+mode), the
  width is calculated by finding the left and right edges, where each edge
  is found by scanning the values from the left and right until the y value
  is above the half maximum. some interpolation is done.
  """

  stdev = numpy.std(yvec)
  mean = numpy.mean(yvec)
  median = numpy.median(yvec)
  mode = STATS.mode(yvec)[0][0]
  peak = max(yvec)
  miny = min(yvec)
  auc = sum(yvec - mode)

  start = None
  end = None

  ret = [peak, miny, median, mean, stdev, auc]

  m = median
  # Assume there is only one peak for now
  if peak > m+2*stdev:
    # use the mode to estimate the noise floor
    hm = mode + 0.5*(peak-mode)
    ret.append(find_width(xvec, yvec, hm))
    ret.append(mode)

  else:
    ret += [None, mode]

  if asdict:
    retdict = {}
    keys = ['max', 'min', 'median', 'mean', 'stdev', 'AUC', 'FWHM', 'mode']
    for key,value in zip(keys, ret):
      retdict[key] = value
    return retdict
  else:
    return ret

def stats(**kwargs):
  csvfile = kwargs['csvfile']
  csvreader = CSVReader(csvfile)
  mat = csvreader.mat

  xvec = mat[:,0]

  def f(key):
    return kwargs[key] or kwargs['all']

  fieldwidth=12
  lblwidth=16

  print csvfile
  print ' '*lblwidth,
  colheaders = ['Max', 'Min', 'Median', 'Mean', 'Stdev', 'AUC', 'FWHM', 'Mode']
  fmt = '%%-%ds'%(fieldwidth)
  for hdr in colheaders:
    print fmt%(hdr) + '|',
  print ''
  print ' '*lblwidth,'-'*(len(colheaders)*(fieldwidth+2)-1)

  def p(yvec):
    #fmt = '%%-%dG'%(fieldwidth)
    fmt = '%%-%dG'%(fieldwidth)
    s = get_stats(xvec, yvec)
    for x in s:
      if x is None:
        x = -1234
      print fmt%(x)+'|',

  ycnt = 1
  fmt = '%%%ds'%(lblwidth)

  colhdrs = csvreader.column_headers
  for yvec in mat.T:
    if len(colhdrs) >= ycnt:
      lbl = colhdrs[ycnt-1]
    else:
      lbl = 'Y%d:'%(ycnt)
    print fmt%(lbl),
    p(yvec)
    print ''
    ycnt+=1

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Computes statistics for F410 scan data')

  parser.add_argument('csvfiles', nargs='+', type=str, help='CSV files to compute statistics for')

  args = vars(parser.parse_args())

  for csvfile in args['csvfiles']:
    args['csvfile'] = csvfile
    stats(**args)
    print ''
