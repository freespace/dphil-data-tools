#!/usr/bin/env python

"""
This script finds peaks by looking for zero-crossing in the 1st derivative.
The x-location of the 10 biggest peaks and their magnitude is printed in order
of descending magnitude
"""

import numpy as NP

def main(filename, *args):
  data = NP.genfromtxt(
      filename,
      delimiter=",",
      dtype=float,
      skip_header=2,
      comments='#')
  if NP.isnan(NP.sum(data)):
    # failed to load psf data using default settings, assuming it is from
    # imageJ and thus tab delimited with no headers
    data = NP.genfromtxt(
        filename,
        dtype=float)

  if NP.isnan(NP.sum(data)):
    print 'nan in data file, aborting'
    return -1

  from stats import get_stats
  xvec = data[:,0]
  yvec = data[:,1]
  dyvec = yvec[1:] - yvec[:-1]

  # 2-tuples of x, amplitude
  peaks = []

  for idx in xrange(len(dyvec)-1):
    if dyvec[idx] >= 0 and dyvec[idx+1] < 0:
      peaks.append((xvec[idx+1], yvec[idx+1]))

  peaks.sort(key=lambda x: x[1], reverse=True)
  for x, y in peaks[:10]:
    print 'y=%.4f\t x=%.4f'%(y,x)

if __name__ == '__main__':
  import sys
  sys.exit(main(*sys.argv[1:]))


