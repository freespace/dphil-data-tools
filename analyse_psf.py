#!/usr/bin/env python
"""
This script looks at the PSF and tells me:
  - FWHM
  - Measure of skew

The measure of skew is based on the shoulder of the PSF, in this particular
case when the up slope exceeds gradient of 1, and  when the down slope becomes
greater than -1. The y coordinate where these crossing occurs should be the
same for a symmetric PSF, otherwise they won't be. The measure of skew is
computed as:

  abs(1-(up_y/down_y))

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
  stats = get_stats(data[:,0], data[:,1], noauc=True)
  FWHM = stats[-1]

  # find the x axis coordinate of when the peak occurs
  peakx = None
  for x,y in data[:]:
    if y >= stats[0]:
      peakx = x
      break

  print 'Peak:', stats[0], 'at x=', peakx
  print 'FWHM:',FWHM


if __name__ == '__main__':
  import sys
  sys.exit(main(*sys.argv[1:]))

