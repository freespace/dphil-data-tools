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
