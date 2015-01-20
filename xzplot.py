"""
This file is a wrapper for plot_plane_using_scans.
"""
import matplotlib.pyplot as plt
from plot2d import plot_plane_using_scans

def plot_xz_plane_using_scans(scanIDs, xposvec, flip_x=False, noarrow=False, um_units=False, **imshowkwargs):
  """
  Plots XZ plane image using scans specified via scanIDs. The x position of
  each scan is given by xposvec, which is 1-1 matched to scanIDs.

  In addition to plotting, the result 2D array is also returned.

  If flip_x is given, scanIDs and xposvec are both reversed.

  If noarrows is True, then arrows indicating ultrasound and flow direction are omitted.

  If um_units is True, then positions are assumed to be specified in um.
  Otherwise they are assumed to be in mm, which is the default.

  Any unknown kwargs are passed onto imshow.
  """

  if flip_x:
    scanIDs = scanIDs[::-1]
    xposvec = xposvec[::-1]

  if um_units:
    labels = ('Z position (um)', 'X position (um)')
  else:
    labels = ('Z position (mm)', 'X position (mm)')

  ret = plot_plane_using_scans(scanIDs,
                               xposvec,
                               labels=labels,
                               um_units=um_units,
                               **imshowkwargs)

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
  ax.text(1, 0.2, 'Flow', rotation=-90, **commonkwargs)

  return ret
