#!/usr/bin/env python
"""
This script takes individual .power.npz files and constructs a spectrogram by
stacking the power spectrum contained in each file.

When binning is performed, the timestamp of a bin is the timestamp of the fist
power spectrum in the bin, and power at each frequency is the _mean_ power at
each frequency of the power spectrums in the bin.

Note that this used to produce spectrograms with a logged colourbar, but this is
a bad idea b/c it sacrifices visibility of high power signals, which is what
we are really interested in. So says Constatine, and I agree.
"""


import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import gridspec

import matplotlib_setup

mpl.rcParams['mathtext.default'] = 'regular'

def savefig(fig, *args, **kwargs):
  if not 'bbox_inches' in kwargs is None:
    kwargs['bbox_inches'] = 'tight'

  fig.savefig(*args, **kwargs)

  print 'Plot saved to file:',args[0]

def _process_data(data, header, highpass):
  hp_filter = data[:,0]<highpass
  freqvec = data[:,0]
  powervec = data[:,1]

  powervec[hp_filter] = 0

  trigtimestr = header['trigtime']

  from datetime import datetime
  # really should standardise on a datetime format, e.g. ISO 8601. However
  # python is unlikely to change how str(datetime) works so this is probably
  # ok for now.
  trigtime = datetime.strptime(trigtimestr, '%Y-%m-%d %H:%M:%S.%f')


  return freqvec, powervec, trigtime

def _data_generator(powerfilevec, **cmdargs):
  head_skip = cmdargs['head_skip']
  ismerged = len(powerfilevec) == 1
  if ismerged:
    print 'Processing merged frequency power data'
    npz = np.load(powerfilevec[0])
    filenamelist = npz.keys()
    print '\t%d merged files'%(len(filenamelist))
    print '\t%d will be skipped'%(head_skip)

    filenamelist.sort()

    for fname in filenamelist[head_skip:]:
      datadict = npz[fname].item()
      data = datadict['data']
      header = datadict['header']
      yield(fname, data, header)
  else:
    powerfilevec.sort()
    for pfile in powerfilevec[head_skip:]:
      npz = np.load(pfile)
      npzfile = np.load(pfile)
      data = npzfile['data']
      header = npzfile['header'].item()
      if type(header) == str:
        import json
        header = json.loads(header)

      yield (pfile, data, header)

def plot_spectrogram(**cmdargs):
  powerfilevec = cmdargs['powerfiles']
  binsize = cmdargs['binsize']
  max_bins = cmdargs['max_bins']
  no_debug = cmdargs['no_debug']
  power_only = cmdargs['power_only']
  max_tduration = cmdargs['max_tduration']
  highpass = cmdargs['highpass']
  spectrogram_max = cmdargs['spectrogram_max']

  binpower = None
  bincount = 0
  bintrigtime = None

  freqvec0 = None

  lastrigtime = None
  starttime = None
  # contains 2-tuple of (trigger time, power spectrum)
  powerspecvec = list()
  spec_count = 0
  for pfile, data, header in _data_generator(powerfilevec, **cmdargs):
    freqvec, powervec, trigtime = _process_data(data, header, highpass)
    spec_count += 1
    # enforce the condition that power spectrums are monotically into the
    # future
    if lastrigtime is not None:
      assert trigtime > lastrigtime, pfile

    if starttime is None:
      starttime = trigtime

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

      if max_bins is not None and len(powerspecvec) >= max_bins:
        break

    if (spec_count+1)%10 == 0:
      import sys
      sys.stdout.write('.')
      sys.stdout.flush()

  print ''

  # if the last bin is not full it will not have been added, so do it now
  if binpower is not None:
    powerspecvec.append((bintrigtime, binpower/bincount))

  # sort by trigger time
  powerspecvec.sort(key=lambda x:x[0])

  tstart = powerspecvec[0][0]
  tend = powerspecvec[-1][0]

  # turn these into MHz
  freqstart = freqvec0[0]/1e6
  freqend = freqvec0[-1]/1e6

  print 'Binned %d power spectrums into %d bins of size %d'%(spec_count, len(powerspecvec), binsize)
  print '   Duration: %s (%s --> %s)'%(tend - tstart, tstart, tend)
  if max_bins is not None:
    print '   Max bins =', max_bins

  spectrogram = np.column_stack(map(lambda x:x[1], powerspecvec))

  tduration = tend - tstart
  tdurationsecs = tduration.total_seconds()

  if max_tduration is not None:
    tdurationsecs = min(tdurationsecs, max_tduration)

  if power_only:
    gs = gridspec.GridSpec(1, 1)
    plt.figure(figsize=(10,5))
  else:
    gs = gridspec.GridSpec(2, 1, height_ratios=[2,1])

    plt.subplot(gs[0])

    vmax = spectrogram_max
    if vmax is None:
       # we use the 99th percentile here as otherwise a single high
       # value will complete ruined the colourmap
      vmax=np.percentile(spectrogram, 99)

    plt.imshow(spectrogram,
               aspect='auto',
               interpolation='none',
               extent=[0, tdurationsecs, freqstart, freqend],
               cmap=cmdargs['cmap'],
               origin = 'lower',          # put low freq near (0,0)
               vmin=spectrogram.min(),
               vmax=vmax,
               )

    plt.ylabel('Frequency (MHz)')

    textvec = ['File: %s'%(powerfilevec[0])]
    if len(powerfilevec) > 1:
      textvec.append('File: %s'%(powerfilevec[-1]))

    textvec.append('cmap=%s'%(cmdargs['cmap']))

    if binsize > 1:
      textvec[-1] += ' binsize=%d'%(binsize)

    textvec.append('start_time=%s'%(starttime))
    if not no_debug:
      plt.text(0.1, 0.1, '\n'.join(textvec), color='0.5')

    plt.grid()

    # SIOS takes scans every 30 s, so lets have 30 s tics
    plt.xticks(np.arange(0, tdurationsecs+1, min(30, tdurationsecs/4)))
    fntsize = 'large'
    title = cmdargs.get('title')
    if len(title) > 60:
      fntsize = 'medium'

    plt.title(title, size=fntsize)

    cbar = plt.colorbar()
    cbar.set_label('Power Density ($V^2/Hz$)')

  ##############################################################################
  power_fit = cmdargs['power_fit']
  power_vlines = cmdargs['power_vlines']
  power_ylim = cmdargs['power_ylim']

  total_power = map(lambda x:np.sum(x[1]), powerspecvec)
  plt.subplot(gs[-1])
  dt = tdurationsecs/len(total_power)
  tvec = np.arange(len(total_power)) * dt
  plt.plot(tvec, total_power)

  plt.xlabel('Time (s)')
  plt.ylabel('Power ($V^2$)')

  if not power_only:
    # add the same color bar as the top graph, then hide it so
    # the top and bottom plot edges line up
    cbar = plt.colorbar()
    cbar.remove()

  if power_fit > 0:
    coeffs = np.polyfit(tvec, total_power, power_fit)
    fitfunc = np.poly1d(coeffs)
    plt.hold(True)
    plt.plot(tvec, fitfunc(tvec), color='k')

  for vl in power_vlines:
    ylim = plt.ylim()
    plt.vlines(vl, ylim[0], ylim[1], linestyle='solid', colors=['r'])

  if power_ylim is not None:
    plt.ylim(power_ylim)

  plt.gca().get_yaxis().grid(True)
  ##############################################################################

  ancillary_data = cmdargs['ancillary_data']
  ancillary_ylabel = cmdargs['ancillary_ylabel']
  ancillary_ylim = cmdargs['ancillary_ylim']
  ancillary_hline = cmdargs['ancillary_hline']
  ancillary_hline2 = cmdargs['ancillary_hline2']
  ancillary_xoffset = cmdargs['ancillary_xoffset']

  if ancillary_data:
    datafile = ancillary_data
    xindex = 1
    yindex = 2

    if datafile[-1] == ']':
      datafile, yindex = datafile.rsplit('[', 1)
      yindex = int(yindex[:-1])

    from dataloader import DataLoader
    loader = DataLoader(datafile)

    xvec = loader.matrix[:,xindex-1] + ancillary_xoffset
    yvec = loader.matrix[:,yindex-1]

    ax = plt.gca()
    ax = ax.twinx()
    ax.plot(xvec, yvec, 'r')
    ax.set_ylabel(ancillary_ylabel)

    if ancillary_ylim is not None:
      ax.set_ylim(ancillary_ylim)

    if ancillary_hline is not None:
      xlim = ax.get_xlim()
      ax.hlines(ancillary_hline, xlim[0], xlim[1], linestyle='dashed', colors=['r'])

    if ancillary_hline2 is not None:
      xlim = ax.get_xlim()
      ax.hlines(ancillary_hline2, xlim[0], xlim[1], linestyle='dashdot', colors=['r'])

  ##############################################################################

  plt.xlim([0, tdurationsecs])
  plt.xticks(np.arange(0, tdurationsecs+1, min(30, tdurationsecs/4)))

  ##############################################################################

  savepdf = cmdargs['pdf']
  savepng = cmdargs['png']
  power_save = cmdargs['power_save']

  shouldshow = not savepdf and not savepng and not power_save

  if shouldshow:
    for fignum in plt.get_fignums():
      from utils import keypress
      fig = plt.figure(fignum)
      fig.canvas.mpl_connect('key_press_event', keypress)

    plt.show()

    # bring the window to front
    cfm = plt.get_current_fig_manager()
    cfm.window.activateWindow()
    cfm.window.raise_()

  import os.path as op
  if len(powerfilevec) > 1:
    firstlast = (powerfilevec[0], powerfilevec[-1])
    firstlast = map(op.basename,firstlast)
    firstlast = map(lambda x:op.splitext(x)[0],firstlast)

    savefile = '%s__%s-spectrogram'%(firstlast[0], firstlast[1])
  else:
    fname, _ = op.splitext(powerfilevec[0])
    fname = op.basename(fname)
    savefile = '%s-spectrogram'%(fname)

  f = plt.figure(plt.get_fignums()[0])

  savefile += '-bin'+str(binsize)
  if power_only:
    savefile += '-ponly'

  if power_fit>0:
    savefile += '-pfit'+str(power_fit)

  for vl in power_vlines:
    savefile += '-vl%.1f'%(vl)

  if ancillary_data:
    savefile += '-ancillary'

  if power_save:
    power_mat = np.column_stack((tvec, total_power))
    powersavefile = savefile + '-power-over-time.npz'
    np.savez_compressed(powersavefile, power_matrix=power_mat, source='plot_spectrogram.py')
    print 'Power curve saved to', powersavefile


  # if we don't do this then the resulting plot isn't long enough to
  # comfortably contain the x axis tick labels
  f.set_size_inches(16, 9)
  if savepng:
    savefig(f, savefile+'.png')
  if savepdf:
    savefig(f, savefile+'.pdf')


def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots spectrogram by combining individual power spectrums')

  parser.add_argument('-title', default='', help='Plot title')
  parser.add_argument('-cmap', default='jet', help='Matplotlib colormap to use, defaults to "jet"')

  parser.add_argument('-binsize', type=int, default=5, help='Perform binning with the given bin size. Bin size does not have to be a integer divisor of the number of samples. Defaults to 5')
  parser.add_argument('-max_bins', type=int, default=601, help='Plot no more than this number of bins. Defaults to 601')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-png', action='store_true', default=False, help='Plot will be saved to PNG instead of being shown')

  parser.add_argument('-no_debug', action='store_true', default=False, help='Debugging information at lower-left will not be plotted.')

  parser.add_argument('-max_tduration', type=float, help='Sets the maximum duration in seconds')

  parser.add_argument('-highpass', type=float, default=0, help='Removes signals below the specified frequency (Hz)')

  parser.add_argument('-spectrogram_max', type=float, default=None, help='Sets the maximum value of the spectrogram')

  parser.add_argument('-power_only', action='store_true', default=False, help='When given only the power-over-time series is plotted')
  parser.add_argument('-power_fit', type=int, default=-1, help='When >0, a polynomial of order n will be fitted to the data')
  parser.add_argument('-power_vlines', nargs='+', default=[], type=float, help='When given a vertical line will be plotted at the specified x position')
  parser.add_argument('-power_save', action='store_true', help='When given the data used to plot the power curve is saved')
  parser.add_argument('-power_ylim', type=float, nargs=2, help='Set y limits of power plot')

  parser.add_argument('-ancillary_data', type=str, default=None, help='Specifies an additional NPZ to plot into the lower power plot using the right y axis. Using [n] notation at the end of the file to specify the Y column index is supported')
  parser.add_argument('-ancillary_ylabel', type=str, default='', help='Specifies y label for ancillary data')
  parser.add_argument('-ancillary_ylim', type=float, nargs=2, help='Set y limits of right axis for ancillary data')
  parser.add_argument('-ancillary_hline', type=float, help='Adds a horizontal line to the ancillary plot')
  parser.add_argument('-ancillary_hline2', type=float, help='Adds a second horizontal line to the ancillary')
  parser.add_argument('-ancillary_xoffset', type=float, help='Offset added to x values of ancillary data')

  parser.add_argument('-head_skip', type=int, default=0, help='Number of files to skip before head of the queue. Files will be sorted before skip is applied. Negative values are allowed, in which case it turns into tail skip')

  parser.add_argument('powerfiles', nargs='+', help='.power.npz files produced by calc_power_spectrum.py')

  return parser

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

if __name__ == '__main__':
  cmdargs = parse_commandline_arguments()
  plot_spectrogram(**cmdargs)

