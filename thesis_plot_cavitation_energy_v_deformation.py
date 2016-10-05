#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

def _load_csv(csv_file):
  # can't use the standard DataLoader b/c I need the text content
  with open(csv_file) as f:
    content = f.read()

  groups = dict()
  for ldx, line in enumerate(content.split('\n')):
    fields = filter(len, map(str.strip, line.split('\t')))

    if len(fields):
      if ldx == 0:
        header = fields
        print header
      else:
        print fields
        experiment_group, phantom_id, thesis_label, cav_energy_V2s, deformation_um = fields

        # group cav:deformation by cavitation nuclei type, which we can infer
        # from the first character of thesis_label
        nuclei_type = thesis_label[0]

        data = map(float, (cav_energy_V2s, deformation_um))
        grp = groups.get(nuclei_type, list())
        assert grp is not None
        grp.append(data)
        groups[nuclei_type] = grp

  # convert each array of (cav_eng, deformation) into a 2 column matrix
  for lbl in groups.keys():
    groups[lbl] = np.asarray(groups[lbl])
  return groups

def main(csv_file=None, pdf=False, png=False, legend=False, logx=False, xlim=None, inset_xlim=None):
  groups = _load_csv(csv_file)
  import matplotlib.pyplot as plt
  import matplotlib_setup

  plt.figure(figsize=(14,10))

  plt.hold(True)

  def plot_grp(ax, grp, marker, label):
    cav_e = grp[:,0]
    deform = grp[:,1]

    cav_e_mean = np.mean(cav_e)
    deform_mean = np.mean(deform)

    print 'group %s: mean energy=%.2f V^2 s, mean deformation=%.2f'%(label, cav_e_mean, deform_mean)

    ax.plot(cav_e, deform, markersize=10, marker=marker, linestyle='None', label=label)
    ax.plot(cav_e_mean, deform_mean, marker=marker, linestyle='None', markersize=15, color='k',
                                                                                      markerfacecolor='None',
                                                                                      markeredgewidth=2)

    ax.get_xaxis().get_major_formatter().set_powerlimits((0, 0))

  markers = ['^', 'o', 's', 'v', 'H', 'p']
  for marker, grp_data in zip(markers, groups.items()):
    grp, data = grp_data
    plot_grp(plt.gca(), data, marker, grp)

  if logx:
    plt.xscale('log')

  if xlim:
    plt.xlim(xlim)

  plt.xlabel('Cavitation Energy ($\mathrm{V}^2\mathrm{s}$)')
  plt.ylabel('Deformation Size (um)')
  plt.grid()

  if legend:
    plt.legend()

  if inset_xlim:
    a2 = plt.axes([0.5, 0.15, 0.36, 0.35])
    for marker, grp_data in zip(markers, groups.items()):
      grp, data = grp_data
      plot_grp(a2, data, marker, grp)
      a2.set_xlim(inset_xlim)
      a2.grid(True)

  if not pdf and not png:
    from utils import keypress
    plt.gcf().canvas.mpl_connect('key_press_event', keypress)
    plt.show()
  else:
    def savefig(fig, *args, **kwargs):
      if not 'bbox_inches' in kwargs is None:
        kwargs['bbox_inches'] = 'tight'

      fig.savefig(*args, **kwargs)

      print 'Plot saved to file:',args[0]

    if png:
      savefig(plt.gcf(), csv_file+'.png')

    if pdf:
      savefig(plt.gcf(), csv_file+'.pdf')

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Integrates power spectrum over time to measure the total detected cavitation energy')
  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-png', action='store_true', default=False, help='Plot will be saved to PNG instead of being shown')
  parser.add_argument('-legend', action='store_true', default=False, help='Legend will be plotted')
  parser.add_argument('-logx', action='store_true', default=False, help='X axis will be plotted log-scale')
  parser.add_argument('-xlim', nargs=2, type=float, default=None, help='Limits of the x axis in')
  parser.add_argument('-inset_xlim', nargs=2, type=float, default=None, help='Limits of the x axis in the inset')
  parser.add_argument('csv_file', type=str, help='CSV file containing cavitation energy and deformation data')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
