""" Module for IO of cache files
"""
import numpy as np

from ..common import log, show_progress, ts2class, ts2doc, ts2dod
from ..common import constants as cons


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
    cache = np.load(_file)
    records = cache['record']
    n = len(records)
    if verbose:
        log.info('Total number of records: {}'.format(n))

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
