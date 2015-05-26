#!/usr/bin/env python

"""
Computes power spectrum. Input files are assumed to contain time in the first
column and some kind of amplitude measurement in the second.

Output will be another csv file that has the same filename but with extension
of power. The first column will be frequency, the second column will be U^2
where U is the unit of measurement in the second column of the input.

The returned power spectrum will be one sided and space delimited.

The sampling rate will be infered from the first 2 entries in the time column
of the input file, i.e. fs = 1/(t[1]-t[0]). An implication of this is that
samples are assumed to be uniform in time.
"""

import numpy as np

OUTPUT_EXT = 'power'

def calc_power_spectrum(x, fs):
  """
  x: data
  fs: sampling frequency

  Data points are assumed to be uniform in time, i.e.
  the time between samples are the same, and is equal to
  1/fs.

  The frequency and the power at each frequency is returned
  as a two-tuple. Note that the two-sided power spectrum is
  returned.
  """
  X = np.fft.fft(x)
  ps = np.abs(X)**2
  freqs = np.fft.fftfreq(x.size, 1.0/fs)
  idx = np.argsort(freqs)

  return freqs[idx], ps[idx]

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computer power spetrum of input files')
  parser.add_argument('inputfiles', nargs='+', help='Files to compute the power spectrum for')
  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()

  import sys
  def p(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')

  from csvtools import CSVReader
  from os.path import splitext, extsep

  for inputfile in cmdargs['inputfiles']:
    reader = CSVReader(inputfile)
    mat = reader.mat
    tvec = mat[:,0]
    xvec = mat[:,1]
    fs = 1.0/(tvec[1]-tvec[0])

    p('Processing %s. Sampling frequency %.2f MHz'%(inputfile, fs/1e6))
    freqs, ps = calc_power_spectrum(xvec, fs)

    # extracted only the one sided spectrum
    onesidedmask = freqs >= 0
    freqs = freqs[onesidedmask]
    ps = ps[onesidedmask]

    filename, ext = splitext(inputfile)
    outputfile = filename + extsep + OUTPUT_EXT

    header = 'Computed from %s sampling freq %.2f Hz'%(inputfile, fs)

    outmat = np.column_stack((freqs, ps))
    np.savetxt(outputfile, outmat, delimiter=' ', header=header)
    p('Wrote power spectrum to %s'%(outputfile))