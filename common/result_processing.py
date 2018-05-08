""" Module for common functions related to processing YATSM results
"""
import math

import numpy as np

from . import ordinal_to_doy
from . import constants as cons


def ts2map(ts_set, _type='change', option=[0]):
    """ generate map class of various type from YATSM time series segments

    Args:
        ts_set (list, ndarray): a set of time series segments for a pixel
        _type (int): type of map to generate
        option (list): map type specific options
    Returns:
        map (int): map value

    """
    if _type == 'change':
        # change map
        map = ts_set[0]['break']
        if map > 0:
            map = 1
    elif _type == 'nchange':
        # number of change
        map = (ts_set[-1]['break'] > 0) + len(ts_set) - 1
    elif _type == 'doc':
        # date of change
        if option[0] == 1:
            if (len(ts_set) > 1) & (ts_set[-1]['break'] == 0):
                map = ts_set[-2]['break']
            else:
                map = ts_set[-1]['break']
        else:
            map = ts_set[0]['break']
        if map > 0:
            map = ordinal_to_doy(map)
    elif _type == 'los':
        # length of segment
        if option[0] == 1:
            map = ts_set[-1]['end'] - ts_set[-1]['start']
        else:
            map = ts_set[0]['end'] - ts_set[0]['start']
    else:
        map = cons.NODATA
    return map


def ts2class(ts, _class, _last):
    """ convert YATSM time series segment to land cover class

    Args:
        ts (ndarray): time series segment record
        _class (int): current class
        _last (bool): is this the last segment for this pixel
    Returns:
        class2 (int): new class

    """
    class2 = classify(ts)
    if class2 == cons.FOREST:
        if (ts['end'] - ts['start']) < cons.LENGTH_THRES:
            if _class == cons.NF:
                if _last:
                    return cons.NF
                else:
                    return cons.PF
            elif _class == con.CHANGE:
                if not _last:
                    return cons.PC
                else:
                    return cons.CHANGE
        if (ts['break'] > 0) & (_last):
            return cons.PC
        else:
            return cons.FOREST
    else:
        if _class == cons.FOREST:
            return cons.CHANGE
        elif _class == cons.PF:
            return cons.NF
        elif _class == cons.PC:
            return cons.CHANGE
        elif _class == cons.NODATA:
            return cons.NF
    return _class


def ts2doc(ts, ts_last, cdate, _last):
    """ get date of change from YATSM time series segment

    Args:
        ts (ndarray): time series segment record
        ts_last(ndarray): last time series segment record
        cdate (int): current change date
        _last (bool): is this the last segment for this pixel
    Returns:
        cdate2 (int): new change date

    """
    _class = classify(ts)
    if _class == cons.FOREST:
        if (ts['end'] - ts['start']) < cons.LENGTH_THRES:
            if cdate != cons.NODATA:
                if classify(ts_last) != cons.FOREST:
                    return cdate
        if (ts['break'] > 0) & (_last):
            return ordinal_to_doy(int(ts['break']))
        else:
            return cons.FOREST
    else:
        if cdate == cons.FOREST:
            return ordinal_to_doy(int(ts_last['break']))
        if cdate == cons.NODATA:
            return cons.NF
    return cdate


def ts2dod(ts, ts_last, ddate, _last):
    """ get date of detection from YATSM time series segment

    Args:
        ts (ndarray): time series segment record
        ts_last (ndarray): last time series segment record
        ddate (int): current detect date
        _last (bool): is this the last segment for this pixel
    Returns:
        ddate2 (int): new detect date

    """
    _class = classify(ts)
    if _class == cons.FOREST:
        if (ts['end'] - ts['start']) < cons.LENGTH_THRES:
            if ddate != cons.NODATA:
                if classify(ts_last) != cons.FOREST:
                    return ddate
        if (ts['break'] > 0) & (_last):
            return ordinal_to_doy(int(ts['detect']))
        else:
            return cons.FOREST
    else:
        if ddate == cons.FOREST:
            return ordinal_to_doy(int(ts_last['detect']))
        if ddate == cons.NODATA:
            return cons.NF
    return ddate


def classify(ts):
    """ classify time series segment

    Args:
        ts (ndarray): time series segment record
    Returns:
        class (int): class

    """
    # calculate segment mean
    x1 = ln_gety(ts['coef'][1,], ts['coef'][0,],
                    (ts['end'] - ts['start']) / 2 + ts['start'])[cons.TEST_BAND]
    # calculate segment amplitude
    x2 = math.sqrt(ts['coef'][2, cons.TEST_BAND] ** 2 + ts['coef'][3,
                    cons.TEST_BAND] ** 2) * 2
    # calculate segment slope
    x3 = abs(ts['coef'][1, cons.TEST_BAND])
    # figure out class of current segment
    if ((x1 >= cons.MEAN_THRES) &
        (x2 < cons.AMP_THRES) &
        (x3 < cons.SLOPE_THRES)):
        return cons.FOREST
    else:
        return cons.NF


def ln_gety(a, b, x):
    """ calculate y from linear model

    Args:
        a (ndarray): slope
        b (ndarray): intercept
        x (ndarray): x
    Returns:
        y (ndarray): y

    """
    return a*x+b
