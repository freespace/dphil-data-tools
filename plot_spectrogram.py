#!/usr/bin/env python
"""
This script takes individual .power.npz files and constructs a spectrogram by
stacking the power spectrum contained in each file.

When binning is performed, the timestamp of a bin is the timestamp of the fist
power spectrum in the bin, and power at each frequency is the mean power at
each frequency of the power spectrums in the bin.
"""

import os.path as op

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['mathtext.default'] = 'regular'

def savefig(fig, *args, **kwargs):
  if not 'bbox_inches' in kwargs is None:
    kwargs['bbox_inches'] = 'tight'

  fig.savefig(*args, **kwargs)

  print 'Plot saved to file:',args[0]

def plot_spectrogram(**cmdargs):
  powerfilevec = cmdargs['powerfiles']
  binsize = cmdargs['binsize']

  binpower = None
  bincount = 0
  bintrigtime = None

  freqvec0 = None

  lastrigtime = None
  # contains 2-tuple of (trigger time, power spectrum)
  powerspecvec = list()
  for pfile in powerfilevec:
    npzfile = np.load(pfile)
    data = npzfile['data']

    # we delibrately ignore the DC signal, b/c it is very small
    # and messes up our plotting when logged
    freqvec = data[1:,0]
    powervec = data[1:,1]

    headerjson = npzfile['header'].item()

    import json
    metadata = json.loads(headerjson)
    trigtimestr = metadata['trigtime']

    from datetime import datetime
    # really should standardise on a datetime format, e.g. ISO 8601. However
    # python is unlikely to change how str(datetime) works so this is probably
    # ok for now.
    trigtime = datetime.strptime(metadata['trigtime'], '%Y-%m-%d %H:%M:%S.%f')

    # enforce the condition that power spectrums are monotically into the
    # future
    if lastrigtime is not None:
      assert trigtime > lastrigtime, pfile
    lastrigtime = trigtime

    if binpower is None:
      binpower = powervec
      bintrigtime = trigtime
      bincount = 1
    else:
      binpower += powervec
      bincount += 1

    if freqvec0 is None:
      freqvec0 = freqvec

    if bincount >= binsize:
      powerspecvec.append((bintrigtime, binpower/bincount))
      binpower = None
      bincount = 0

  # if the last bin is not full it will not have been added, so do it now
  if binpower is not None:
    powerspecvec.append((bintrigtime, binpower/bincount))

  tstart = powerspecvec[0][0]
  tend = powerspecvec[-1][0]

  # turn these into MHz
  freqstart = freqvec0[0]/1e6
  freqend = freqvec0[-1]/1e6

  print 'Binned %d power spectrums into %d bins'%(len(powerfilevec), len(powerspecvec))
  print '   Time: %s --> %s'%(tstart, tend)

  spectrogram = np.column_stack(map(lambda x:x[1], powerspecvec))

  tduration = tend - tstart
  tdurationsecs = tduration.total_seconds()

  plt.imshow(spectrogram,
             aspect='auto',
             interpolation='none',
             extent=[0, tdurationsecs, freqstart, freqend],
             cmap=cmdargs['cmap'],
             norm=mpl.colors.LogNorm(), # logs the colour values
             origin = 'lower',          # put low freq near (0,0)
             vmin=1e-7,
             vmax=1,
             )

  textvec = ['File: %s'%(powerfilevec[0])]
  textvec.append('File: %s'%(powerfilevec[-1]))
  textvec.append('cmap=%s'%(cmdargs['cmap']))
  if binsize > 1:
    textvec[-1] += ' binsize=%d'%(binsize)

  plt.text(0.1, 0.1, '\n'.join(textvec))

  plt.xlabel('Time (s)')
  plt.ylabel('Frequency (MHz)')

  plt.grid()

  # SIOS takes scans every 30 s, so lets have 30 s tics
  plt.xticks(np.arange(0, tdurationsecs+1, min(30, tdurationsecs/4)))
  plt.title(cmdargs.get('title', ''))

  cbar = plt.colorbar()
  cbar.set_label('$log(V^2)$')

  savepdf = cmdargs['pdf']
  shouldshow = not savepdf

  if shouldshow:
    for fignum in plt.get_fignums():
      from utils import keypress
      fig = plt.figure(fignum)
      fig.canvas.mpl_connect('key_press_event', keypress)

    plt.show()
  else:
    import os.path as op
    firstlast = (powerfilevec[0], powerfilevec[-1])
    firstlast = map(op.basename,firstlast)
    firstlast = map(lambda x:op.splitext(x)[0],firstlast)

    pdffile = '%s__%s-spectrogram.pdf'%(firstlast[0], firstlast[1])

    f = plt.figure(plt.get_fignums()[0])
    f.set_size_inches(16, 9)
    savefig(f, pdffile)

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots spectrogram by combining individual power spectrums')

  parser.add_argument('-title', default='', help='Plot title')
  parser.add_argument('-cmap', default='jet', help='Matplotlib colormap to use, defaults to "jet"')

  parser.add_argument('-binsize', type=int, default=1, help='Perform binning with the given bin size. Bin size does not have to be a integer divisor of the number of samples')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')

  parser.add_argument('powerfiles', nargs='+', help='.power.npz files produced by calc_power_spectrum.py')

  return parser

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

if __name__ == '__main__':
  cmdargs = parse_commandline_arguments()
  plot_spectrogram(**cmdargs)

