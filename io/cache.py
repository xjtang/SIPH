""" Module for IO of cache files
"""
import numpy as np

from ..common import log, show_progress, ts2class, ts2doc
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
        if _type == 'cls':
            line[px] = ts2class(ts, line[px])
        elif _type == 'doc':
                line[px] = ts2doc(ts, line[px])
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
        return line.astype(np.int32)
    else:
        return line.astype(np.int16)
