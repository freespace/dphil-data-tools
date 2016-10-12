#!/usr/bin/env python
"""
Intended as a replacement for gnuplot. As such it supports different separator
characters, plotting multiple series, etc.

Since this script is intended for mywork there are certain presets which may
or may not be useful to a general user.
"""

from __future__ import division

import os.path as op

import numpy as np
import matplotlib.pyplot as PLT

import matplotlib_setup

from utils import keypress

class CSVProxy(object):
  mat = None
  comments = None
  csv_source = None

import itertools
linestyles = ['-', '--', '-.', ':']
markerstyles = ['o', 'v','^', 's', 'p', '*', 'h', 'H', '+', 'x', 'D']
linecolors = ['b', 'r', 'g', 'c', 'm', 'orange', 'k']
linespecs = list(itertools.product(linestyles, markerstyles, linecolors))
linespec_idx = 0

def reset_linespec():
  global linespec_idx
  linespec_idx = 0

def _next_linespec():
  global linespec_idx
  ls = list(linespecs[linespec_idx])
  ls[1], ls[2] = ls[2], ls[1]
  linespec_idx = (linespec_idx+1)%len(linespecs)
  return ls

class Plot(object):
  def __init__(self, **kwargs):
    super(Plot, self).__init__()
    self._kwargs= kwargs

    self._fig = kwargs.get('fig', PLT.gcf())
    if self._fig is None:
      self._fig = PLT.gcf()
      if self._fig is None:
        self._fig = PLT.figure()

    # don't use the default kwargs of get to add subplot because
    # order of evaluation is not guaranteed and it has side effects
    self._ax = kwargs.get('ax')
    if self._ax is None:
      self._ax =self._fig.add_subplot(111)

    self.plotkwargs = {
        'solid_capstyle':'butt',
        'markersize':self.markersize,
        'linewidth':1.2,
        }
    self.textkwargs = {
        'transform':self._ax.transAxes,
        'size': 11,
        }

    # tstart of the first trace
    self._tstart0 = self.t0

    # whether we are plotting a single csv file
    self._single = len(self.csvfiles) == 1


  def __getattr__(self, attr):
    if attr in self._kwargs:
      return self._kwargs[attr]
    else:
      raise AttributeError('No attribute named %s found'%(attr))

  def _get_save_to_filename(self, ext):
    filename = self.filename
    csvfiles = self.csvfiles
    suffix = list()

    if self.normalise:
      suffix.append('NR')

    if self.sub_y0:
      suffix.append('SUBY0')

    if self.sub_x0:
      suffix.append('SUBX0')

    if self.register_on_ymax:
      suffix.append('REGYMAX')

    if self.xoffset != 0:
      suffix.append('XOFF')

    if self.ymultiplier != 1.0:
      suffix.append('YMULT')

    if self.xmultiplier != 1.0:
      suffix.append('XMULT')

    if self.yindex is not 2:
      suffix.append('YIDX%d'%(self.yindex))

    if self.ylim is not None:
      suffix.append('%.2fY%.2f'%(self.ylim[0], self.ylim[1]))

    if self.right_ylim is not None:
      suffix.append('%.2fRY%.2f'%(self.right_ylim[0], self.right_ylim[1]))

    if self.xlim is not None:
      suffix.append('%.2fX%.2f'%(self.xlim[0], self.xlim[1]))

    if self.differentiate:
      suffix.append('DY')

    if len(suffix):
      suffix = '-'.join(suffix)
      suffix = '-' + suffix
    else:
      suffix = ''
    suffix += '.'+ext

    if filename is None:
      startfile = op.splitext(csvfiles[0])[0]

      # the file might have a path in it. We discard it so the output
      # is always in the directory we are currently in
      startfile = op.basename(startfile)

      if len(csvfiles) == 1:
        filename = startfile + suffix
      else:
        endfile = op.splitext(op.basename(csvfiles[-1]))[0]
        # assuming these are SIOS scans, which they most likely are, then we
        # only need the first 7 + 3 + 1 = 11 characters to unique identify
        # the file
        endfile = endfile[:11]

        filename = startfile+'__'+endfile+suffix
    else:
      filename += suffix

    # it is entirely possible to end up with more than 255 characters, which
    # is more than any FS currently in use supports, so we truncate the
    # middle.
    maxlen = 128
    if len(filename) >= maxlen:
      middle = '_TRUNCATED_'
      l = (maxlen - len(middle))//2

      start = filename[:l]
      end = filename[-l:]

      filename = start + middle + end

    return filename

  def savefig(self, *args, **kwargs):
    if not 'bbox_inches' in kwargs is None:
      kwargs['bbox_inches'] = 'tight'

    self._fig.savefig(*args, **kwargs)
    print 'Plot saved to file:',args[0]

  def save_to_pdf(self):
    pdfname = self._get_save_to_filename('pdf')
    self.savefig(pdfname)

  def save_to_png(self):
    pngname = self._get_save_to_filename('png')
    self.savefig(pngname, dpi=300)

  def show(self):
    fig = self._fig

    fig.canvas.mpl_connect('key_press_event', keypress)

    # on OS X the tk window is behind everyone else by default, so we use
    # apple scripting to bring it to the front
    # http://stackoverflow.com/questions/1892339/make-tkinter-jump-to-the-front
    #
    # This stopped working for me in OS X 10.9.3, so I am disabling it
    #import sys
    #if sys.platform == 'darwin':
    #  import os
    #  os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

    PLT.show()

  def _make_tstart_label(self, tstart):
    if self._tstart0 is None:
      self._tstart0 = tstart
    tstart -= self._tstart0
    return 't=%.1f s'%(tstart)

  def _plot_traces(self, lbl, xvec, yvec, tvec, yerr=None, use_right=False):
    if self.negoverflow:
      print 'Fixing negative overflow assuming +/-10V range'
      # b/c of exposure control, the accumulated reading value can exceed
      # positive limit of the signed 16bit value that stores readings on
      # the ADC.  However because we only have VOLTAGES, we cannot simply
      # cast to unsigned to fix the issue.
      #
      # Instead we have to do our own wrapping, where -9V is really 11V that
      # overflowed. The easiest way to do this is to add to 20 the negative
      # value, which is intutitively the same thing.

      def f(v):
        if v < 0:
          v = 20 + v
        return v
      posyvec = [f(v) for v in yvec]
      yvec = posyvec

    if self.lowpass is not None:
      print 'Low pass filtering with cutoff at %.2f Hz'%(self.lowpass)

      from lowpass import lowpassfilter

      # For now, we will assume that sample spacing is constant in time as
      # well as in space. This isn't true, but SIOS doesn't have the ability
      # right now to log the time between samples.
      #
      # However in future if we do have sampling time for each sample, we will
      # want to use it, so put in a warning if we detect we have unique sample
      # times for each sample
      if len(np.unique(tvec)) == len(tvec):
        print '!! WARNING !! Sampling times available but being ignored'

      dt = np.abs(tvec[0] - tvec[-1])
      nsamples = len(yvec)
      sampling_rate = nsamples / dt

      print '%d samples over %.2f seconds = %.2f Hz sampling rate'%(nsamples, dt, sampling_rate)

      filteredyvec = lowpassfilter(yvec, sampling_rate, self.lowpass)

      yvec = filteredyvec

    xnew = xvec
    ynew = yvec

    if self.interp == True:
      print 'Interpolation ON'

      from scipy.interpolate import interp1d
      # first down sample to smooth out the data
      interpf = interp1d(xvec, yvec, kind='cubic')
      xnew = np.linspace(xvec.min(), xvec.max(), len(xvec)/2)
      ynew = interpf(xnew)

      # now up sample it to make it it look smooth
      interpf = interp1d(xnew, ynew, kind='cubic')
      xnew = np.linspace(xvec.min(), xvec.max(), len(xvec))
      ynew = interpf(xnew)

    l = None

    # give precedence to generated or user supplied labels
    if lbl is not None:
      l = lbl

    ls, lc, marker = _next_linespec()
    if self.linestyles is not None:
      if len(self.linestyles) == 1:
        ls = self.linestyles[0].strip()
      else:
        ls = self.linestyles.pop(0).strip()

    if self.markerstyles is not None:
      if len(self.markerstyles) == 1:
        marker = self.markerstyles[0].strip()
      else:
        marker = self.markerstyles.pop(0).strip()

    # make errorbar color more transparent so we can see the actual data
    from matplotlib import colors
    ecolor = colors.colorConverter.to_rgba(lc, 0.5)

    # if we have a lot of data, then reduce error bar density
    errorevery = 1
    if (len(ynew) > 100):
      errorevery = 2

    ax = self._ax

    if use_right:
      ax = ax.twinx()
      ax.set_ylabel(self.right_ylabel)
      if self.right_ylim:
        ax.set_ylim(*self.right_ylim)

    ax.errorbar(xnew,
                ynew,
                linestyle=ls,
                color=lc,
                marker=marker,
                label=l,
                yerr=yerr,
                ecolor=ecolor,
                errorevery=errorevery,
                **self.plotkwargs)


  def plot(self):
    """
    This function is *wayyyyyy* too long
    """
    csvfiles = self.csvfiles
    title = self.title
    title = title.replace('\\n', '\n')

    fig = self._fig
    ax = self._ax

    headers = ['']

    ylim = self.ylim

    if self.labels is None and len(csvfiles) > 1:
      # if no labels are specified and we have multiple
      # csv files, then when we plot it is confusing which
      # trace corresponds to which file. In these cases
      # we populate the labels with the basename of the csvfiles
      self.labels = map(op.basename, csvfiles)

      # shorten/truncate filenames in the legend if they are over 16
      # characters
      def shorten(s):
        from os.path import splitext
        s = splitext(s)[0]
        if len(s) > 32:
          return s[:10]+'..'+s[-16:]
        else:
          return s
      self.labels = map(shorten, self.labels)

    if ylim is not None:
      ax.set_autoscaley_on(False)
      ax.set_ylim(ylim)

    for csvidx in xrange(len(csvfiles)):
      if self.color_cycle_length is not None:
        # the first +1 is to stop csvidx=0 from triggering even
        # though it has no ill effect. The second +1 is because to
        # have a cycle length of 3, e.g. 0,1,2 you need to reset
        # on the 4, not 3
        if (csvidx+1)%(self.color_cycle_length+1) == 0:
          reset_linespec()

      from dataloader import DataLoader
      csvfile = csvfiles[csvidx]

      csv_ydx = None
      if csvfile.endswith(']'):
        csvfile, ydx = csvfile.rsplit('[', 1)
        csv_ydx = int(ydx[:-1])

      print 'Plotting',csvfile
      data = DataLoader(csvfile)
      print 'Data source', data.source

      pathcomponents = op.abspath(csvfile).split(op.sep)
      filespec = op.sep.join(pathcomponents[-4:])
      if len(pathcomponents) > 4:
        filespec = '...'+filespec

      headers += ['# File: '+filespec]
      if self._single:
        headers.append(data.header)

      if self.labels is not None:
        if csvidx < len(self.labels):
          lbl = self.labels[csvidx]
        else:
          lbl = self.labels[-1]
      else:
        lbl = None

      xvec = data.matrix[:,self.xindex-1]

      ydx = self.yindex-1
      if csv_ydx is not None:
        ydx = csv_ydx-1

      print 'Using y-index:',ydx+1
      yvec = data.matrix[:,ydx]

      yerr = None
      if self.yerror_index is not None:
        yerr = data.matrix[:, self.yerror_index-1]

      if data.source == 'SIOS':
        tvec = csv.mat[:,3]
      else:
        tvec = None

      if data.source == 'calc_power_spectrum.py':
        xvec /= 1000
        self.logy = True

      if self.register_on_ymax:
        maxidx = np.argmax(yvec)
        xvec -= xvec[maxidx]

      if self.sub_x0:
        xvec -= xvec[0]

      if self.sub_y0:
        yvec -= yvec[0]

      xvec += self.xoffset

      xvec *= self.xmultiplier
      yvec *= self.ymultiplier

      if self.normalise:
        yrange = yvec.max() - yvec.min()
        yvec -= yvec.min()
        yvec /= yrange

      if self.differentiate:
        dy = yvec[1:] - yvec[:-1]
        yvec = dy
        xvec = xvec[1:]
        print 'Differentiating'

      use_right = self.use_right_axis_for == csvfile
      self._plot_traces(lbl, xvec, yvec, tvec, yerr=yerr, use_right=use_right)

      if self.fwhm:
        from stats import get_stats
        sdict = get_stats(xvec, yvec, asdict=True)
        FWHM = sdict['FWHM']
        fstart, fend = sdict['FWHM_x']
        hm = yvec.max()/2
        ax.hlines(hm, fstart, fend, linewidth=4, linestyles='solid', colors=['black'])
        ax.text((fstart+fend)/2, hm*0.9, '%.2f'%(FWHM), size=11, ha='center')

    if self.logy == True:
      ax.set_yscale('log')

    xlabel, ylabel = data.xy_labels

    if self.xlabel is not None:
      xlabel = self.xlabel
    if self.ylabel is not None:
      ylabel = self.ylabel

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if self.no_legend == False:
      if self.labels is not None:
        if len(self.labels) > 5:
          fontsize = 8
        else:
          fontsize = 11

        ax.legend(
            loc=self.legend_position,
            ncol=1,
            prop={'size':fontsize})

    ax.set_title(title, size='medium')
    ax.set_autoscalex_on(False)

    # set x and y limits if given
    if self.xlim is not None:
      ax.set_xlim(self.xlim)

    def get_ticks(start, end, step):
      assert end > start
      diff = end - start
      ticks = np.arange(diff // step) * step + start
      return np.append(ticks, [end])

    if self.xtic_step is not None:
      minx, maxx = ax.get_xlim()
      ax.set_xticks(get_ticks(minx, maxx, self.xtic_step))

    if self.ytic_step is not None:
      miny, maxy = ax.get_ylim()
      ax.set_yticks(get_ticks(miny, maxy, self.ytic_step))

    yaxis = ax.get_yaxis()
    xaxis = ax.get_xaxis()

    ylim = yaxis.get_view_interval()
    xlim = xaxis.get_view_interval()

    if self.hgrid or self.grid:
      yaxis.grid()

    if self.vgrid or self.grid:
      xaxis.grid()

    if self.vline is not None:
      for vl in self.vline:
        ax.vlines(vl, ylim[0], ylim[1], linestyles='solid', colors=['red'])

    if self.hline is not None:
      for hl in self.hline:
        ax.hlines(hl, xlim[0], xlim[1], linestyles='solid', colors=[self.hline_color])

    if self.normalise:
      ax.hlines(0.5, xlim[0], xlim[1], linestyles='dotted', colors=['gray'])

    texttoplot = ['']
    # comments needs to be a list
    if self.comments is not None:
      texttoplot.extend(map(lambda x: '# '+x, self.comments))

    if self.negoverflow:
      texttoplot.append('# Negative overflows fixed')
    if self.lowpass is not None:
      texttoplot.append('# '+'Lowpass filtered at %.2f Hz'%(self.lowpass))

    if not self.no_debug:
      texttoplot.extend(headers)

    ax.text(
        0, 1.0,
        '\n'.join(texttoplot),
        color='0.75',
        zorder=-1,
        verticalalignment='top',
        **self.textkwargs)

    # resize the plot if figsize is given
    if self.figsize is not None:
      fig.set_size_inches(*self.figsize, forward=True)
      PLT.tight_layout()

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='GNUplot replacement plotter')

  parser.add_argument('-title', default='', help='Plot title')

  parser.add_argument('-linestyles', nargs='+', default=None, help='If given, data series will be rendered using the specified linestyle. If number of series exceeds number of linestyles, then the last given linestyle will be used for the remaining series.')

  parser.add_argument('-markerstyles', nargs='+', default=None, help='If given, data series will be rendered using the specified linestyle. If the number of series execeeds the number of markerstyles, then the last given markerstyle will be used for the remaining series')
  parser.add_argument('-markersize', type=float, default=4.0, help='Specifies the size of markers, defaults to 1.0')

  parser.add_argument('-color_cycle_length', type=int, default=None, help='If given, the colors will reset and cycle from the beginning every n data series')
  parser.add_argument('-show_start_time', action='store_true', help='If given, the time of the first csv file will be shown as a label in the top-right.')
  parser.add_argument('-t0', type=float, default=None, help='Value to use as t=0 when displaying time points on the x-axis.')
  parser.add_argument('-x0', type=float, default=None, help='Value to use as x=0 when displaying positions on the x-axis. ')
  parser.add_argument('-no_debug', action='store_true', help='If given, file comments and filenames will not be added to plots.')

  parser.add_argument('-sub_x0', action='store_true', help='If given, the first x value is subtracted from all x values')
  parser.add_argument('-sub_y0', action='store_true', help='If given, the first y value is subtracted from all y values')

  parser.add_argument('-register_on_ymax', action='store_true', help='If given, the x value at which y is maximum will be subtracted from all x value, effectively putting the maximum y value at x=0')

  parser.add_argument('-xoffset', type=float, default=0, help='Value to add to all x values. Applied before xmultiplier.')

  parser.add_argument('-xmultiplier', type=float, default=1, help='Value to multiplu x by before plotting. This happens after sub_x0.')
  parser.add_argument('-ymultiplier', type=float, default=1, help='Value to multiplu y by before plotting. This happens after sub_y0.')

  parser.add_argument('-differentiate', action='store_true', help='If given the dy/dx plotted, where dy=dy[n]-dy[n-1], dx=x[n]-x[n-1]')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-png', action='store_true', default=False, help='Plot will be saved to PNG instead of being shown')
  parser.add_argument('-filename', default=None, type=str, help='Name of output file to write to. Defaults to name of the first and last csv file joined by double underscore (__)')

  parser.add_argument('-xindex', type=int, default=1, help='Index of column (1..) to use for x axis')
  parser.add_argument('-yindex', type=int, default=2, help='Index of colunm (1..) to use for y axis')

  parser.add_argument('-xlabel', type=str, default='', help='X label.')
  parser.add_argument('-ylabel', type=str, default='', help='Y label.')
  parser.add_argument('-right_ylabel', type=str, default='',  help='Right Y label.')

  parser.add_argument('-legend_position', type=str, default='best', help='Matplotlib position to put the legend, defaults to "upper right". Note this must be quoted')
  parser.add_argument('-labels', type=str, nargs='+', help='Labels for each series to use in the legend. If there are not enough labels for series, then the last label is repeated.')
  parser.add_argument('-no_legend', action='store_true', default=False, help='If given no legend will be plotted.')

  parser.add_argument('-normalise', action='store_true', default=False, help='If given, the y-values will be normalised to be between [0..1].')

  parser.add_argument('-logy', action='store_true', default=False, help='If given, the y-axis will be log')
  parser.add_argument('-yerror_index', type=int, default=None, help='If given, errorbars will be plotted using data in the specified column (1..)')

  parser.add_argument('-ylim', type=float, nargs=2, default=None, help='If given, the y limits will be as given')
  parser.add_argument('-right_ylim', type=float, nargs=2, default=None, help='If given, the right y axis limits will be as given')
  parser.add_argument('-xlim', type=float, nargs=2, default=None, help='If given, the x limits will be as given')

  parser.add_argument('-xtic_step', type=float, default=None, help='If given, xtics will be this this far apart')
  parser.add_argument('-ytic_step', type=float, default=None, help='If given, ytics will be this this far apart')

  parser.add_argument('-hgrid', action='store_true', default=False, help='If given, horizontal grid will be added.')
  parser.add_argument('-vgrid', action='store_true', default=False, help='If given, vertical grid will be added.')
  parser.add_argument('-grid', action='store_true', default=False, help='If given, vertical grid will be added.')

  parser.add_argument('-vline', type=float, nargs='+', default=None, help='If given, a vertical line in red will be plotted at the specified x coordinate. Specify multiple x values to plot multiple lines.')
  parser.add_argument('-hline', type=float, nargs='+', default=None, help='If given, a horizontal line in will be plotted at the specified y coordinate. Specify multiple y values to plot multiple lines.')
  parser.add_argument('-hline_color', type=str, default='red', help='Specifies the colour of hlines, defaults to red')

  parser.add_argument('-fwhm', action='store_true', default=False, help='If given, FWHM will be computed and plotted.')
  parser.add_argument('-figsize', type=float, nargs=2, default=None, help='If given, the figure size will be set as given, in inches')

  parser.add_argument('-interp', action='store_true', default=False, help='If given, each series will be interpolated using a cubic')
  parser.add_argument('-lowpass', type=float, default=None, help='If given, each series will be low pass filtered, with the cutoff as specified in Hz. When used wit interp, low pass filtering occurs first')
  parser.add_argument('-negoverflow', action='store_true', default=False, help='If given negative values will be assumed to be overflows from +10, and will be fixed accordingly. This occurs before filtering and interpolation')

  parser.add_argument('-use_right_axis_for', type=str, default=None, help='If given, the specified file will be plotted using the RIGHT Y axis')

  parser.add_argument('-plotfile', type=str, default=None, help='A file containing the filenames of csvs to plot, along with optional title and comments')

  parser.add_argument('-skip', type=int, nargs=1, default=[0], help='When given a skip of n, every nth file is plotted, all other files with the exception of the first and last, is skipped.')

  parser.add_argument('-max_traces', type=int, nargs=1, default=[-1], help='When given, no more than max_traces number of traces will be plotted')
  parser.add_argument('-start_offset', type=int, nargs=1, default=[0], help='When given, the first start_offset number of files are ignored. This is applied before skip is applied')
  parser.add_argument('-include_first_last', action='store_true', default=False, help='If given, the first and last csv given is always plotted, regardless of skip, max_traces, or start_offset')

  parser.add_argument('-comments', type=str, nargs='+', default=None, help='If given, will be displayed in top left of plot in background. Not affected by -no_debug')
  parser.add_argument('csvfiles', nargs='+', help='CSV/npz/trc files to plot. Append [n], e.g. filename.npz[n], to use the nth column. This overrides the -yindex value. 1-based.')

  return parser


if __name__ == '__main__':
  cmdargs = parse_commandline_arguments()

  plotfile = cmdargs['plotfile']
  if plotfile:
    from plotfiletools import parse_plotfile
    csvfiles, moreargs = parse_plotfile(plotfile)
    import sys

    # this order should give precedence to commandline args
    newargs = moreargs + sys.argv[1:]
    cmdargs = vars(parser.parse_args(newargs))
    l = cmdargs.get('csvfiles')
    if l is None:
      cmdargs['csvfiles'] = csvfiles
    else:
      l.extend(csvfiles)

  csvfiles = cmdargs['csvfiles']

  firstcsv = csvfiles[0]
  lastcsv = csvfiles[-1]

  # apply start_offset
  start_offset = cmdargs['start_offset'][0]
  csvfiles = csvfiles[start_offset:]

  # apply skip
  skip = cmdargs['skip'][0]
  last = csvfiles[-1]
  csvfiles = csvfiles[0::skip+1]

  # apply max_traces
  max_traces = cmdargs['max_traces'][0]
  if max_traces >= 0:
    csvfiles = csvfiles[:max_traces]

  if cmdargs['include_first_last']:
    if not csvfiles[0] == firstcsv:
      csvfiles.insert(0, firstcsv)

    if not csvfiles[-1] == lastcsv:
      csvfiles.append(lastcsv)

  if len(csvfiles) < 1:
    print 'No files to plot: no files given or start_offset is too high or max_traces is 0'

  cmdargs['csvfiles'] = csvfiles

  p = Plot(**cmdargs)
  p.plot()

  shouldshow = True
  if cmdargs['pdf']:
    p.save_to_pdf()
    shouldshow = False

  if cmdargs['png']:
    p.save_to_png()
    shouldshow = False

  if shouldshow:
    p.show()

