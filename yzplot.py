"""
This file is a wrapper for plot_plane_using_scans.
"""
from matplotlib import pyplot as plt
from plot2d import plot_plane_using_scans

def plot_yz_plane_using_scans(scanIDs, yposvec, noarrow=False, **imshowkwargs):
  """
  Plots YZ plane image using scans specified via scanIDs. The y position of
  each scan is given by yposvec, which is 1-1 matched to scanIDs.

  In addition to plotting, the result 2D array is also returned.

  If noarrows is True, then arrows indicating ultrasound and flow direction are omitted.
  noarrows is automatically true of imagej_compat of imshowkwargs is True.

  Any unknown kwargs are passed onto imshow.
  """

  labels = ('Z position (mm)', 'Y position (mm)')

  ret = plot_plane_using_scans( scanIDs,
                                yposvec,
                                labels=labels,
                                **imshowkwargs)

  if not noarrow and not imshowkwargs.get('imagej_compat', False):
    ax = plt.gca()
    bbox_props = dict(boxstyle='larrow,pad=0.3', fc='white', ec='k', lw=2)
    fontdict = dict(weight='bold')

    commonkwargs = dict(bbox=bbox_props,
                        fontdict=fontdict,
                        transform=ax.transAxes,
                        va='bottom',
                        ha='right',
                        size=10)

    ax.text(1, 0.1, 'Ultrasound', **commonkwargs)
    ax.text(1, 0.2, 'Gravity', rotation=90, **commonkwargs)

  return ret
