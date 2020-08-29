"""
load_track.py

Imports GPS tracking data (from CSV) generated by the Columbus V990
GPS logger
"""

import sys as _sys
from datetime import datetime as _datetime
import numpy as _np
import pandas as _pd


def v990_to_float(col, ctype='lat'):
    """
    Convert a V990 data column from string to float. Also apply correct +/-
    sign depending on suffix.

    Parameters:
    - col: numpy array of strings to be converted
    - ctype: 'lat' or 'lon'. Sets the conversion of N/S to +/- or E/W to +-/,
             as appropriate
    """

    if ctype == 'lat':
        negdir = 'S'
    elif ctype == 'lon':
        negdir = 'W'
    else:
        _sys.stderr.write("Error: ctype must be either 'lat' or 'lon'\n")
        return _np.nan * _np.zeros_like(col)

    numval = _np.array([float(x.decode()[:-1]) for x in col])
    sign = _np.array([-1 if x.decode()[-1] == negdir else 1 for x in col])

    return sign * numval

def v990_assemble_date(date, time):
    """
    Take the date and time columns and convert them into a singe list of python
    datetime objects.
    """

    assert len(date) == len(time), "date and time must be the same length."

    dates = [_datetime.strptime(date[i].decode()+time[i].decode(),
                                "%y%m%d%H%M%S") for i in range(len(date))]

    return dates


def load_track(fname, average=False):
    """
    Load a CSV file generated by the V-990 and convert it into a pandas
    dataframe

    Parameters:
    - fname: name/path for the CSV file with GPS log information
    - average: if True, average readings in blocks of 8 (for spy mode)
    """

    dtype = [('date', 'S6'),
             ('time', 'S6'),
             ('lat', 'S14'),
             ('lon', 'S14'),
             ('height', 'S8'),
             ('speed', 'S8'),
             ('PDOP', 'S8'),
             ('HDOP', 'S8'),
             ('VDOP', 'S8')]

    sdtype = [('lat', float),
              ('lon', float),
              ('height', float),
              ('speed', float),
              ('PDOP', float),
              ('HDOP', float),
              ('VDOP', float)]

    raw = _np.genfromtxt(fname,
                         delimiter=',',
                         skip_header=1,
                         usecols=(2, 3, 4, 5, 6, 7, 11, 12, 13),
                         dtype=dtype)

    # first we need to convert some objects to numeric types
    lat = v990_to_float(raw['lat'], ctype='lat')
    lon = v990_to_float(raw['lon'], ctype='lon')
    height = _np.array([float(x.decode()) for x in raw['height']])
    speed = _np.array([float(x.decode()) for x in raw['speed']])
    PDOP = _np.array([float(x.decode()) for x in raw['PDOP']])
    HDOP = _np.array([float(x.decode()) for x in raw['HDOP']])
    VDOP = _np.array([float(x.decode()) for x in raw['VDOP']])

    if average:
        if len(raw) % 8:
            _sys.stderr.write("Error: averaging requested, but the number \
of points is not a multiple of 8.\n")
            return -1
        nmeas = int(len(raw) / 8)
        conv = _np.ones(nmeas,
                        dtype=sdtype)
        ndates = []
        ntimes = []
        for i in range(nmeas):
            if _np.median(speed[i*8:(i+1)*8]) > 0.0:
                _sys.stderr.write("Median speed not zero for a dataset. \
skipping")
                conv[i]['lat'] = _np.nan
                conv[i]['lon'] = _np.nan
                conv[i]['speed'] = _np.nan
                conv[i]['height'] = _np.nan
                ndates.append(raw['date'][i+3])
                ntimes.append(raw['time'][i+3])
            else:
                conv[i]['lat'] = _np.mean(lat[i*8:(i+1)*8])
                conv[i]['lon'] = _np.mean(lon[i*8:(i+1)*8])
                conv[i]['speed'] = 0.0
                conv[i]['height'] = _np.mean(height[i*8:(i+1)*8])
                # TODO: should really do a proper computation of the mean time
                ndates.append(raw['date'][i+3])
                ntimes.append(raw['time'][i+3])
        dates = v990_assemble_date(ndates, ntimes)
    else:
        conv = {'lat': lon,
                'lon': lat,
                'height': height,
                'speed': speed,
                'PDOP': PDOP,
                'HDOP': HDOP,
                'VDOP': VDOP}
        dates = v990_assemble_date(raw['date'],
                                   raw['time'])

    df = _pd.DataFrame(data=conv,
                       index=dates)

    return df
