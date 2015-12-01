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

start_time: start time of ultrasound exposure. The first value in the time
column is not necessarily 0 due to time-offset of the oscilloscope. This
should be specified in the same time units as the input.

exposure_duration: length of ultrasound exposure in the same time units as the
input.

start_time and exposure_duration combine to form a window, and only the signal
inside the window is computed. No windowing function is done.

Both start_time and exposure_duration support the use of suffixes:
  - m: units of 1e-3
  - u: units of 1e-6
  - n: units of 1e-9

e.g. 3u specifies 3e-6.

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
  returned, and the output has been normalised by the number
  elements in x.
  """
  X = np.fft.fft(x)
  ps = np.abs(X)**2
  freqs = np.fft.fftfreq(x.size, 1.0/fs)
  idx = np.argsort(freqs)

  return freqs[idx], ps[idx]/len(x)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computer power spetrum of input files')
  parser.add_argument('start_time', type=str, help='Start time of ultrasound exposure')
  parser.add_argument('exposure_duration', type=str, help='Ultrasound exposure time')
  parser.add_argument('inputfiles', nargs='+', help='Files to compute the power spectrum for')
  return parser

def parse_number(s):
  suffix = s[-1]
  if suffix.isdigit():
    return float(s)
  else:
    number = float(s[:-1])
    if suffix == 'm':
      number *= 1e-3
    elif suffix == 'u':
      number *= 1e-6
    elif suffix == 'n':
      number *= 1e-9
    else:
      assert False

    return number

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()

  import sys
  def p(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')

  from csvtools import CSVReader
  from os.path import splitext, extsep

  start_time = parse_number(cmdargs['start_time'])
  exposure_duration = parse_number(cmdargs['exposure_duration'])
  end_time = start_time + exposure_duration

  for inputfile in cmdargs['inputfiles']:
    p('Loading %s'%(inputfile))

    if inputfile.endswith('csv'):
      p('  CSV')
      reader = CSVReader(inputfile)
      mat = reader.mat
      tvec = mat[:,0]
      xvec = mat[:,1]
    elif inputfile.endswith('trc'):
      p('  Lecroy')
      from lecroy import read_timetrace
      tvec, xvec = read_timetrace(inputfile)
      print tvec.shape, xvec.shape

    nsamples = len(tvec)

    windowmask = np.logical_and(tvec >= start_time, tvec < end_time)

    tvec = tvec[windowmask]
    xvec = xvec[windowmask]

    windownsamples = len(tvec)
    windowpc = 100.0*windownsamples/nsamples
    p('\tWindow: %.2f us --> %.2f us'%(tvec[0]*1e6, tvec[-1]*1e6))
    p('\t%d samples in window, %d samples total, (%.2f%%)'%(windownsamples, nsamples, windowpc))

    fs = 1.0/(tvec[1]-tvec[0])

    p('\tProcessing at %.2f MHz sampling frequency'%(fs/1e6))
    freqs, ps = calc_power_spectrum(xvec, fs)

    # extracted only the one sided spectrum
    onesidedmask = freqs >= 0
    freqs = freqs[onesidedmask]
    ps = ps[onesidedmask]

    filename, ext = splitext(inputfile)
    outputfile = filename + extsep + OUTPUT_EXT

    headers = ['Computed from %s sampling freq %.2f Hz'%(inputfile, fs)]
    headers.append('Window: %f --> %f'%(start_time, end_time))
    header = '\n'.join(headers)

    outmat = np.column_stack((freqs, ps))
    np.savetxt(outputfile, outmat, delimiter=' ', header=header)
    p('\tWrote power spectrum to %s'%(outputfile))
