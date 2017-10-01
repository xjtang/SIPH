""" Module for common functions related to processing YATSM results
"""
import math

import numpy as np

from . import ordinal_to_doy
from . import constants as cons


def ts2class(ts, _class):
    """ read a csv file based table to a list

    Args:
        ts (ndarray): time series segment record
        _class (int): current class
    Returns:
        class2 (int): new class

    """
    class2 = classify(ts)
    if class2 == cons.FOREST:
        if _class == cons.NODATA:
            return cons.FOREST
    else:
        if _class == cons.FOREST:
            return cons.CHANGE
        elif _class == cons.NODATA:
            return cons.NF
    return _class


def ts2doc(ts, cdate):
    """ read a csv file based table to a list

    Args:
        ts (ndarray): time series segment record
        cdate (int): current change date
    Returns:
        cdate2 (int): new change date

    """
    _class = classify(ts)
    if _class == cons.NF:
        if cdate == cons.NODATA:
            return cons.NF
        elif cdate == cons.FOREST:
            return ordinal_to_doy(int(ts['start']))
    else:
        if cdate == cons.NODATA:
            return cons.FOREST
    return cdate


def ts2dod(ts, ts_last, ddate):
    """ read a csv file based table to a list

    Args:
        ts (ndarray): time series segment record
        ts_last (ndarray): last time series segment record
        ddate (int): current detect date
    Returns:
        ddate2 (int): new detect date

    """
    _class = classify(ts)
    if _class == cons.NF:
        if ddate == cons.NODATA:
            return cons.NF
        elif ddate == cons.FOREST:
            return ordinal_to_doy(int(ts_last['detect']))
    else:
        if ddate == cons.NODATA:
            return cons.FOREST
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
