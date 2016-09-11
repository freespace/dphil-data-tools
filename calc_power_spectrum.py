#!/usr/bin/env python

"""
Computes power spectrum.

Inputs can be CSV files or Lecroy trc files.

Output will be a csv file that has the same filename but with extension
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

Merged NPZ
==========

When -merge is used, the output is a single NPZ file containing. Each filename
becomes a key, and under the key is stored a dictionary containing the keys:

  - header: a dictionary containing metadata
  - source: string identifying the source of the data
  - data: numpy array

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

  Data is zero'd by subtracting the median x value before
  calculation of frequency contents. Doing so removes the
  DC components which is often very large.

  The frequency and the power at each frequency is returned
  as a two-tuple. Note that the two-sided power spectrum is
  returned, and the output has been normalised by the number
  elements in x.

  Note that the output has units of [x]^2/fs aka [x]^2 * T
  where T is the sampling period. This is because to get the
  power of the time domain signal, you need to extract the
  area under the curve, which means assuming the value sampled
  at t is constant over the sampling period T (=1/fs).

  Due to Parsvel's theorem, the power in the time domain (x^2*T)
  must equal to the power in the frequency domain (X^2*T), so
  we have to multiply by T(=1/fs) when we are done. If [x] is Volts
  then we end up with the "expected" power unit V^2/Hz since we divide
  by fs, the sampling frequency (which is equiv to multiplying by T).
  """
  x -= np.mean(x)
  X = np.fft.fft(x)
  ps = np.abs(X)**2 / fs
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
  parser.add_argument('-npz', action='store_true', help='If given output will be .power.npz instead of csv')
  parser.add_argument('-suffix', type=str, default='', help='If given output will be added to file name just before .power')
  parser.add_argument('-merge', action='store_true', help='If given, output will be merged into a single npz')
  parser.add_argument('-glob', type=str, default='*', help='If input is a zip file, this is a unix shell glob pattern to match files for processing')

  return parser

def parse_number(s):
  # negative values are specified by doing \\- or '\-' so the \ is
  # left in and we transparently remove it
  if s[0] == '\\':
    s = s[1:]

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

import sys
def p(s):
  sys.stderr.write(s)
  sys.stderr.write('\n')

def _process_data(inputfile, tvec, yvec, trigtime, **cmdargs):
  start_time = parse_number(cmdargs['start_time'])
  exposure_duration = parse_number(cmdargs['exposure_duration'])
  end_time = start_time + exposure_duration

  nsamples = len(tvec)

  windowmask = np.logical_and(tvec >= start_time, tvec < end_time)

  tvec = tvec[windowmask]
  yvec = yvec[windowmask]

  windownsamples = len(tvec)
  windowpc = 100.0*windownsamples/nsamples
  p('\tWindow: %.2f us --> %.2f us'%(tvec[0]*1e6, tvec[-1]*1e6))
  p('\t%d samples in window, %d samples total, (%.2f%%)'%(windownsamples, nsamples, windowpc))

  fs = 1.0/(tvec[1]-tvec[0])

  p('\tProcessing at %.2f MHz sampling frequency'%(fs/1e6))
  freqs, ps = calc_power_spectrum(yvec, fs)

  # extracted only the one sided spectrum
  onesidedmask = freqs >= 0
  freqs = freqs[onesidedmask]
  ps = ps[onesidedmask]

  metadata = dict(input_file=inputfile,
                  sampling_freq=fs,
                  window=(start_time,end_time),
                  trigtime=str(trigtime))
  outmat = np.column_stack((freqs, ps))

  datadict = dict(data=outmat, header=metadata, source='calc_power_spectrum.py')
  return datadict

def _loadtrc(fname, fcontent):
  p('Loading %s'%(fname))
  from dataloader import DataLoader
  data = DataLoader(fname, fcontent)
  tvec = data.matrix[:, 0]
  yvec = data.matrix[:, 1]
  if data.source == 'LECROYWR104Xi_binary':
    trigtime = data.source_obj.TRIG_TIME
  else:
    trigtime = None

  return tvec, yvec, trigtime

def _generate_data(inputfilelist, glob):
  iszip = inputfilelist[0].endswith('zip')

  if iszip:
    from zipfile import ZipFile
    import fnmatch
    zf = ZipFile(inputfilelist[0])
    filenamelist = fnmatch.filter(zf.namelist(), glob)
    for filename in filenamelist:
      filecontent = zf.read(filename)
      tvec, yvec, trigtime = _loadtrc(filename, filecontent)
      yield filename, tvec, yvec, trigtime
  else:
    for inputfile in inputfilelist:
      tvec, yvec, trigtime = _loadtrc(inputfile)
      yield inputfile, tvec, yvec, trigtime

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  should_merge = cmdargs['merge']

  mergedict = dict()
  suffix = cmdargs['suffix']

  from os.path import splitext, extsep, basename
  inputfilelist = cmdargs['inputfiles']
  for datatuple in _generate_data(inputfilelist, cmdargs['glob']):
    datadict = _process_data(*datatuple, **cmdargs)
    inputfile = datatuple[0]

    if should_merge:
      mergedict[inputfile] = datadict
    else:
      filename, _ = splitext(inputfile)
      filename = basename(filename)
      outputfile = filename + suffix + extsep + OUTPUT_EXT

      if cmdargs['npz']:
        np.savez_compressed(outputfile, **datadict)
        p('\tWrote power spectrum to %s.npz'%(outputfile))
      else:
        import json
        header = json.dumps(datadict['header'])
        outmat = datadict['data']
        np.savetxt(outputfile, outmat, delimiter=' ', header=header)
        p('\tWrote power spectrum to %s'%(outputfile))

  if should_merge:
    if len(inputfilelist) > 1:
      filename0, _ = splitext(inputfilelist[0])
      filenamelast, _ = splitext(inputfilelist[-1])
      filename0, filenamelast = map(basename, (filename0, filenamelast))
      name = filename0 + '__' + filenamelast
    else:
      name = basename(inputfilelist[0])

    outputfile = name + suffix + extsep + OUTPUT_EXT

    np.savez_compressed(outputfile, **mergedict)
    p('Saved merged data to %s.npz'%(outputfile))

