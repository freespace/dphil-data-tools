#!/usr/bin/env python
from os.path import basename

import numpy as np
from scipy import stats as sstats
import matplotlib.pyplot as plt

import dphil_paths

from csvtools import CSVReader

def find_width(xvec, yvec, ytarget):
  """
  Finds distance between 2 points on a curve described by xvec and yvec
  where yvec is greater than ytarget.

  The distance returned is defined to be the distance between the first point of
  3 points to the left of the maximum y value that is below ytarget, and the
  first of 3 points to the right of the same that is below ytarget. This method
  avoids some issues with noisy data.

  returns the width, xstart, xend
  """
  idx_of_max = yvec.argmax()

  start = None
  end = None

  def ylookahead(startidx, steps):
    endidx = startidx + steps
    if endidx < startidx:
      startidx,endidx = endidx, startidx
    for idx in xrange(startidx, endidx):
      if yvec[idx] > ytarget:
        return False
    return True

  # get left position
  idx = idx_of_max
  lookahead = 3
  while idx > lookahead-1:
    if ylookahead(idx, -3):
      start = xvec[idx]
      break
    idx -= 1

  # get right position
  idx = idx_of_max
  while idx < yvec.size-lookahead-1:
    if ylookahead(idx, 3):
      end = xvec[idx]
      break
    idx += 1

  if start is not None and end is not None:
    # take the abs value because sometimes our z values
    # are in descending order because a scan is taken
    # backwards
    return abs(end - start), start, end
  else:
    return None, None, None

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
    - FWHM_x, contains values that bound the computed FWHM

  FWHM is calculated by finding the "half maximum" as 0.5*(peak+mode), the
  width is calculated by finding the left and right edges, where each edge
  is found by scanning the values from the left and right until the y value
  is above the half maximum.
  """

  stdev = np.std(yvec)
  mean = np.mean(yvec)
  median = np.median(yvec)
  mode = sstats.mode(yvec)[0][0]
  peak = max(yvec)
  miny = min(yvec)
  auc = sum(np.abs(yvec))

  start = None
  end = None

  ret = [peak, miny, median, mean, stdev, auc]

  m = median
  # Assume there is only one peak for now
  if peak > m+2*stdev:
    hm = peak/2.0
    fwhm, xstart, xend = find_width(xvec, yvec, hm)
    ret.append(fwhm)
    ret.append([xstart, xend])

  else:
    ret += [None, None]

  if asdict:
    retdict = {}
    keys = ['max', 'min', 'median', 'mean', 'stdev', 'AUC', 'FWHM', 'FWHM_x']
    for key,value in zip(keys, ret):
      retdict[key] = value
    return retdict
  else:
    return ret

def print_stats(**kwargs):
  csvfile = kwargs['csvfile']

  from dataloader import DataLoader
  data = DataLoader(csvfile)

  mat = data.matrix
  xvec = mat[:,0]

  def f(key):
    return kwargs[key] or kwargs['all']

  fieldwidth=12
  lblwidth=16

  statkeys = kwargs['stats']
  if statkeys is not None:
    statkeys = map(str.strip, statkeys.split(','))

  csv_out = kwargs['csv_out']

  print csvfile,

  if csv_out:
    print ',',
  else:
    print 'statistics:'
    print ' '*lblwidth,

  colheaders = ['Max', 'Min', 'Median', 'Mean', 'Stdev', 'AUC', 'FWHM', 'Mode']
  if statkeys is not None:
    colheaders = statkeys

  if not csv_out:
    fmt = '%%-%ds'%(fieldwidth)
    for hdr in colheaders:
      print fmt%(hdr) + '|',
    print ''
    print ' '*lblwidth,'-'*(len(colheaders)*(fieldwidth+2)-1)

  def p(yvec):
    #fmt = '%%-%dG'%(fieldwidth)
    fmt = '%%-%dG'%(fieldwidth)
    if statkeys is not None:
      sdict = get_stats(xvec, yvec, asdict=True)
      colheaders = statkeys
      for sk in statkeys:
        assert sk in sdict, 'Unknown stat %s, available: %s'%(sk, sdict.keys())

      s = map(lambda x: sdict[x], statkeys)
    else:
      s = get_stats(xvec, yvec)
    for x in s:
      try:
        float(x)
      except:
        x = -1234

      if csv_out:
        print x,
        if not s[-1] == x:
          print ',',
      else:
        print fmt%(x)+'|',

  ycnt = 1
  fmt = '%%%ds'%(lblwidth)

  colhdrs = data.xy_labels
  toplot = mat.T
  yindex = kwargs['yindex']
  if yindex is not None:
    toplot = [toplot[yindex]]
    colhdrs = [colhdrs[yindex]]

  for yvec in toplot:
    if len(colhdrs) >= ycnt:
      lbl = colhdrs[ycnt-1]
    else:
      lbl = 'Y%d:'%(ycnt)

    if not csv_out:
      print fmt%(lbl),

    p(yvec)

    if not csv_out:
      print ''

    ycnt+=1

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Computes statistics for F410 scan data')

  parser.add_argument('-stats', default=None, type=str, help='stats to compute. Only these stats will be emitted. Multiple stats can be specified, separated by comma')
  parser.add_argument('-yindex', default=None, type=int, help='Index of Y series data to compute stats for. Defaults to all Y series data.')
  parser.add_argument('-csv_out', default=False, action='store_true', help='If true output will be in CSV format.')
  parser.add_argument('csvfiles', nargs='+', type=str, help='CSV files to compute statistics for')

  args = vars(parser.parse_args())

  if args.get('csv_out') and args.get('yindex') is None:
    import sys
    warning = 'Warning: csv_out specified but yindex is not!'
    sys.stderr.write('\n' + '*'*len(warning) + '\n')
    sys.stderr.write(warning)
    sys.stderr.write('\n' + '*'*len(warning) + '\n\n')

  for csvfile in args['csvfiles']:
    args['csvfile'] = csvfile
    print_stats(**args)
    print ''
