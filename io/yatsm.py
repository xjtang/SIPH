""" Module for IO of YATSM files
"""
import numpy as np

from ..common import log, show_progress, ts2map, ts2class, ts2doc, ts2dod
from ..common import constants as cons


def yatsm2records(_file, verbose=False):
    """ read YATSM result file as a list

    Args:
        _file (str): path to yatsm file
        verbose (bool): verbose or not

    Returns:
        records (ndarray): yatsm records

    """
    yatsm = np.load(_file)
    ks = list(yatsm.keys())
    if 'record' in ks:
        records = yatsm['record']
    else:
        records = yatsm[ks[0]]
    n = len(records)
    if verbose:
        log.info('Total number of records: {}'.format(n))
    return records


def yatsm2pixels(_file, x=[], verbose=False):
    """ read YATSM result file and arrange by pixel

    Args:
        _file (str): path to yatsm file
        x (list/int): which pixels to grab, [] for all
        verbose (bool): verbose or not

    Returns:
        pixels (ndarray): records of selected pixels

    """
    if type(x) == int:
        x = [x]
    pixels = []
    records = yatsm2records(_file, verbose)
    if len(records) > 0:
        pxs = np.unique(records['px'])
        for px in pxs:
            if (px in x) or (len(x)==0):
                pixels.append(records[records['px']==px])
    return pixels


def yatsm2map(_file, _type, samples, option=[0], verbose=False):
    """ calculate map results form cache file

    Args:
        _file (str): path to cache file
        _type (str): map type
        samples (int): number of samples
        option (list): map specific options
        verbose (bool): verbose or not

    Returns:
        line (list): result

    """
    # initialoze result
    if verbose:
        log.info('Initializing result...')
    line = np.zeros(samples) + cons.NODATA

    # read in cache file
    if verbose:
        log.info('Reading in YATSM result file...')
    records = yatsm2records(_file, True)

    # record by record processing
    if verbose:
        log.info('Generating map...')
    ts_set = [records[0]]
    px = ts_set[0]['px']
    for i in range(1, n):
        ts = records[i]
        if px == ts['px']:
            ts_set.append(ts)
        else:
            line[px] = ts2map(ts_set, _type, option)
            ts_set = [ts]
            px = ts['px']
        if verbose:
            progress = show_progress(i, n, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))

    # done
    if verbose:
        log.info('process completed')
    if (_type == 'change' or _type == 'nchange' or _type == 'class'):
        return line.astype(np.int16)
    else:
        return line.astype(np.int32)


def cache2map(_file, _type, samples, verbose=False):
    """ calculate map results form cache file

    Args:
        _file (str): path to cache file
        _type (str): map type
        samples (int): number of samples
        verbose (bool): verbose or not

    Returns:
        line (list): result

    """
    # initialoze result
    if verbose:
        log.info('Initializing result...')
    line = np.zeros(samples) + cons.NODATA

    # read in cache file
    if verbose:
        log.info('Reading in cache file...')
    records = yatsm2records(_file, True)

    # record by record processing
    if verbose:
        log.info('Generating map...')
    for i in range(0,n):
        ts = records[i]
        px = ts['px']
        _last = True
        if i < n - 1:
            if records[i + 1]['px'] == px:
                _last = False
        if i > 0:
            ts_last = records[i - 1]
        else:
            ts_last = ts
        if _type == 'cls':
            line[px] = ts2class(ts, line[px], _last)
        elif _type == 'doc':
            line[px] = ts2doc(ts, ts_last, line[px], _last)
        elif _type == 'dod':
            line[px] = ts2dod(ts, ts_last, line[px], _last)
        else:
            log.error('Unknown type: {}'.format(_type))
            return line
        if verbose:
            progress = show_progress(i, n, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))

    # done
    if verbose:
        log.info('process completed')
    if _type == 'cls':
        return line.astype(np.int16)
    else:
        return line.astype(np.int32)
