import matplotlib.pyplot as plt
import sys

# on OS X we are not getting keypress events with the default backend, but we
# do with tkinter
plt.switch_backend('tkAgg')
def keypress(event):
  if event.key == 'q':
    import sys
    sys.exit(0)

spinner_cnt = 0
def do_spinner(text=''):
  global spinner_cnt

  c = '|'*spinner_cnt
  o = '[%-10s] %s'%(c, text)
  sys.stdout.write(o)
  sys.stdout.write('\b'*len(o))
  sys.stdout.flush()

  spinner_cnt = (spinner_cnt+1)%11

def savefig(filename, silent=False, confirm=True):
  """
  Wrapper around matplotlib's savefig with some common options built in

  If silent is True, then 'Saved to....' will not be emitted.

  If confirm is False, then the user will not be asked to confirm the
  operation. There is a 5s timeout on the confirmation on unix platforms
  only.

  """
  if confirm:
    try:
      import sys, select
      print '\nSave to', filename, '? [Y/n](5s timeout): ',
      sys.stdout.flush()
      i, o, e = select.select([sys.stdin], [], [], 10)
      if i is not None:
        l = sys.stdin.readline().strip()
        if len(l) and l in 'nN':
          return
    except Exception, ex:
      print ex
      return

  plt.savefig(filename, dpi=300, bbox_inches='tight')
  if not silent:
    print 'Saved to', filename
