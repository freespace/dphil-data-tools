#!/usr/bin/env python

"""
This script is used to compute regions of "activity", defined as been
bracketed by y peaks above some threshold.

This is used during alignment to fine tune the position of the pinhole. As
alignment improves, the "ringing" due to diffraction rings will occur
closer and closer together, until it disappears. This script is
to quantify the width of the ringing.
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
  stats = get_stats(xvec, yvec, noauc=True)
  ymax, ymin, ymedian = stats[:3]

  leftedge = None
  rightedge = None

  quartermax = 0.25*(ymax + ymedian)
  for idx in xrange(len(yvec)):
    if yvec[idx] > quartermax:
      leftedge = xvec[idx]
      break

  for idx in xrange(len(yvec)-1, -1, -1):
    if yvec[idx] > quartermax:
      rightedge = xvec[idx]
      break

  print 'Quartermax = ', quartermax
  print 'Width of Region of Interest:', rightedge-leftedge

if __name__ == '__main__':
  import sys
  sys.exit(main(*sys.argv[1:]))


