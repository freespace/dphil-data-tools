#!/usr/bin/env python
import numpy as np

class DataLoader(object):
  """
  This class abstract the process of loading data from a variety of formats,
  including CSVs and NPZ, generated by different data sources.
  """
  _datafilepath = None

  # data matrix
  matrix = None

  # string identifying the source of the data
  source = None

  # object representing the source data, if any
  source_obj = None

  # metadata etc as a string, which is sometimes a JSON
  # string
  header = ''

  # labels for the x and y axys
  xy_labels = None

  def __init__(self, datafilepath, file_content=None):
    """
    Creates a data loader for the given file. The resulting object
    will expose:
      - matrix: numpy array
      - source: string identifying source of the data, determined from content
                and extension of datafilepath
      - header: data metadata as a string, which maybe a JSON string.
      - source_obj: an object representing the data, which may provide
                   additional information. This may be None

    datafilepath: path to the datafile
    file_content: content of the file. If given no attempt will be made to load
                 the file from disk
    """

    self._datafilepath = datafilepath

    matrix = None
    source = None
    source_obj = None
    header = ''
    xylabel = 'X LABEL', 'Y LABEL'

    if file_content:
      toload = file_content
    else:
      toload = datafilepath

    if datafilepath.endswith('csv'):
      import csvtools
      csv = csvtools.CSVReader(toload)
      matrix = csv.mat
      source = csv.csv_source
      header = csv.column_headers

    if datafilepath.endswith('trc'):
      from lecroy import LecroyBinaryWaveform
      bwave = LecroyBinaryWaveform(datafilepath, file_content)
      matrix = bwave.mat
      source = 'LECROYWR104Xi_binary'
      source_obj = bwave
      xylabel = 'Time (seconds)', 'Voltage (V)'

    if datafilepath.endswith('.npz'):
      npzfile = np.load(toload)
      if 'source' in npzfile:
        source = npzfile['source'].item()
      else:
        source = None

      if source is None:
        # assume this is from SIOS
        source = 'SIOS'
        scandata = npzfile['scandata'].item()
        matrix = scandata.matrix
        header = scandata.comments
        xylabel = 'Z position (um)', '%s position (um)'%(scandata.w)
        source_obj = scandata

      if datafilepath.endswith('.power.npz'):
        matrix = npzfile['data']
        header = npzfile['header'].item()
        if source is None:
          source = 'calc_power_spectrum.py'
        xylabel =  'Frequency (KHz)', '$V^{\ 2}$'

      if source == 'wzextract.py':
        matrix = npzfile['data']
        header = npzfile['header'].item()
        xylabel = 'Z position (um)', 'PMT Voltage (V)'

      if source == 'average_traces.py':
        matrix = npzfile['data']
        header = npzfile['header'].item()

      if source == 'integrate_power_spectrum.py':
        matrix = npzfile['data']
        header = npzfile['header'].item()
        xylabel = 'Time (s)', 'Energy ($V^{\ 2}$)'

      if source == 'savgol.py':
        matrix = npzfile['data']
        header = npzfile['header'].item()
        xylabel = 'Z Position (um)', 'PMT Voltage (V)'

    if header is None:
      header =''

    if type(header) in (dict, list):
      import json
      header = json.dumps(header, indent=1, sort_keys=True)

    assert matrix is not None
    assert type(header) == str

    self.matrix = matrix
    self.header = header
    self.source = source
    self.source_obj = source_obj
    self.xy_labels = xylabel
