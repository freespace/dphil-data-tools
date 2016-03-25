# on OS X we are not getting keypress events with the default backend, but we
# do with tkinter
import sys
import matplotlib.pyplot as plt
if sys.platform == 'darwin':
  # backends we want in order of preference
  backendvec = ['Qt5Agg', 'Qt4Agg', 'QtAgg', 'TkAgg']

  for backend in backendvec:
    try:
      plt.switch_backend(backend)
      print 'Using backend',backend
      break
    except:
      pass
