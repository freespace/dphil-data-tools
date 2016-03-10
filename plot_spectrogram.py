#!/usr/bin/env python
"""
This script takes individual .power.npz files and constructs
a spectrogram by stacking the power spectrum contained in each file.
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

  # contains 2-tuple of (trigger time, power spectrum)
  powerspecvec = list()
  for pfile in powerfilevec:
    npzfile = np.load(pfile)
    data = npzfile['data']
    headerjson = npzfile['header'].item()

    import json
    metadata = json.loads(headerjson)
    trigtimestr = metadata['trigtime']

    from datetime import datetime
    # really should standardise on a datetime format, e.g. ISO 8601. However
    # python is unlikely to change how str(datetime) works so this is probably
    # ok for now.
    trigtime = datetime.strptime(metadata['trigtime'], '%Y-%m-%d %H:%M:%S.%f')

    powerspecvec.append((trigtime, data))

  tstart = powerspecvec[0][0]
  tend = powerspecvec[-1][0]

  # turn these into KHz
  freqstart = powerspecvec[0][1][0,0]/1000
  freqend = powerspecvec[0][1][-1,0]/1000

  print 'Got %d power spectrums, starting from %s, ending at %s'%(len(powerspecvec),
                                                                  tstart,
                                                                  tend)

  spectrogram = np.column_stack(map(lambda x:x[1][:,1], powerspecvec))

  tduration = tend - tstart
  tdurationsecs = tduration.total_seconds()

  plt.imshow(spectrogram,
             aspect='auto',
             interpolation='none',
             extent=[0, tdurationsecs, freqstart, freqend],
             cmap='hot',
             norm=mpl.colors.LogNorm())
  plt.xlabel('Time (s)')
  plt.ylabel('Frequency (KHz)')

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
    savefig(f, pdffile)

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots spectrogram by combining individual power spectrums')

  parser.add_argument('-title', default='', help='Plot title')

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

