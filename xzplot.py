"""
This file is a wrapper for plot_plane_using_scans.
"""
from plot2d import plot_plane_using_scans

def plot_xz_plane_using_scans(scanIDs, xposvec, flip_x=False, **imshowkwargs):
  """
  Plots XZ plane image using scans specified via scanIDs. The x position of
  each scan is given by xposvec, which is 1-1 matched to scanIDs.

  In addition to plotting, the result 2D array is also returned.

  If flip_x is given, scanIDs and xposvec are both reversed.

  Any unknown kwargs are passed onto imshow.
  """

  if flip_x:
    scanIDs = scanIDs[::-1]
    xposvec = xposvec[::-1]

  labels = ('Z position (mm)', 'X position (mm)')
  return plot_plane_using_scans(  scanIDs,
                                  xposvec,
                                  labels=labels,
                                  **imshowkwargs)
