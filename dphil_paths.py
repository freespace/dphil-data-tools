#!/usr/bin/env python
from os import getenv
# we will need WZScanData from SIOS
SIOS_PATH=getenv('SIOS_PATH')

# we will also need the stats module from data analysis tools
DATA_TOOLS_PATH=getenv('DPHIL_BIN')

import sys

if SIOS_PATH is None or DATA_TOOLS_PATH is None:
  print 'Please set environmental variables SIOS_PATH and DPHIL_BIN'
  sys.exit(1)

sys.path = SIOS_PATH.split(';') + sys.path
sys.path.insert(0, DATA_TOOLS_PATH)
