import matplotlib.pyplot as plt
import sys

# on OS X we are not getting keypress events with the default backend, but we
# do with tkinter
if sys.platform == 'darwin':
  plt.switch_backend('tkAgg')

def keypress(event):
  """
  Use this to enable pressing 'q' to quit matplotlib:

    fig.canvas.mpl_connect('key_press_event', keypress)

  """
  if event.key == 'q':
    plt.close()
spinner_cnt = 0
def do_spinner(text=''):
  global spinner_cnt

  c = '|'*spinner_cnt
  o = '[%-10s] %s'%(c, text)
  sys.stdout.write(o)
  sys.stdout.write('\b'*len(o))
  sys.stdout.flush()

  spinner_cnt = (spinner_cnt+1)%11

def add_title_legend(fig=plt.gcf(), nrows=1, xpos=0.5, ypos=1.1):
  """
  This adds a legend to where the title would be, using nrow number of rows.

  Lines with get_visible() == False will not be considered
  """
  lines = list()
  for ax in fig.get_axes():
    lines += ax.get_lines()

  oklines = filter(lambda x:x.get_visible(), lines)

  labels = [l.get_label() for l in oklines]
  ncol = max(1, int(len(lines)/nrows))

  fig.get_axes()[0].legend(
      oklines,
      labels, 
      loc='upper center',
      bbox_to_anchor=(xpos, ypos),
      ncol=ncol)

def savefig(filename, formats=None, figure=None, silent=False, pixelsize_um=None):
  """
  Wrapper around matplotlib's savefig with some common options built in

  If figure is given, then the figure's savefig function will be used.
  Otherwise plt.savefig will be used.

  If silent is True, then 'Saved to....' will not be emitted.

  If formats is given as a list, then for each entry, a new filename is
  generated by joining filename with the entry, with a '.' in between. A
  savefig operation is then performed with this new filename. This allows
  for saving multiple formats in one go.

  Note that if the destination already exists, saving will not occur.
  """
  if formats is None:
    filenamevec = [filename]
  else:
    filenamevec = list()

    if type(formats) == str:
      formats = [formats]
    for fmt in formats:
      filenamevec.append(filename + '.' + fmt)

  from os.path import exists
  for fname in filenamevec:
    if exists(fname):
      print 'Not saving to %s, file exists'%(fname)
    else:
      if figure is None:
        figure = plt.gcf()

      print figure.get_figwidth()
      print figure.get_figheight()

      if pixelsize_um is not None:
        dpi = 1000*25.4/pixelsize_um
      else:
        dpi = None

      figure.savefig(fname, dpi=dpi, bbox_inches='tight')

      if not silent:
        print 'Saved to', fname
