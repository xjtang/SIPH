""" Module for reverse classify YATSM results from maps

    Args:
        -p (pattern): searching pattern
        -s (start): start year of the annual maps
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        map: stacked annual land cover map
        des: destination

"""
import os
import sys
import argparse

import numpy as np

from ...common import (log, get_files, manage_batch, enlarge, get_int,
                        ordinal_to_doy, ndarray_append, split_doy)
from ...io import stackGeo, stack2array, yatsm2pixels, chkExist


def reverse_classify(pattern, ori, lc, des, _start=2000, overwrite=False,
                        recursive=False, batch=[1,1]):
    """ reverse classify YATSM results

    Args:
        pattern (str): searching pattern, e.g. yatsm_r*.npz
        ori (str): place to look for inputs
        lc (str): path to stacked annual land cover maps
        des (str): output path and filename
        _start (int): start year
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error when reading annual lc
        5: error when processing

    """
    # check if output exists, if not try to create one
    if chkExist(des, True) > 0:
        if not overwrite:
            return 1

    # locate files
    log.info('Locating files...')
    try:
        yatsm_list = get_files(ori, pattern, recursive)
        n = len(yatsm_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # read stacked annual land cover
    log.info('Reading stacked anual land cover maps: {}'.format(lc))
    try:
        geo = stackGeo(lc)
        lc_stack = stack2array(lc, 0, np.int8)
        if lc_stack.shape[0] < n:
            log.error('Number of lines do not match: {}'.format([n,
                                                            lc_stack.shape[0]]))
            return 4
    except:
        log.error('Failed to read: {}'.format(lc))
        return 4

    # handle batch processing
    if batch[1] > 1:
        log.info('Handling batch process...')
        yatsm_list = manage_batch(yatsm_list, batch[0], batch[1])
        n = len(yatsm_list)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    py, px = (-1, -1)
    log.info('Start reverse classifying pixels...')
    for yatsm in yatsm_list:
        try:
            py = get_int(yatsm[1])[0]
            log.info('Processing line {}'.format(py))
            records = np.load(os.path.join(yatsm[0], yatsm[1]))['record']
            for record in records:
                px = record['px']
                record['class'] = rev_class(record, lc_stack[py, px, :], _start)
            np.savez(os.path.join(des, 'yatsm_r{}.npz'.format(py)),
                        record=records)
            count += 1
        except:
            log.warning('Failed to process line {} pixel {}.'.format(py, px))
            continue

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


def rev_class(x, lc, lc_start):
    """ reverse classify YATSM record

    Args:
        x (ndarray): YATSM record
        lc (list, int): annual land cover classes of a pixel
        lc_start (int): start year of annual land cover

    Returns:
        pixel (list, ndarray): pixel with land cover modified

    """
    ts_start = split_doy(ordinal_to_doy(x['start']))[0]
    ts_end = split_doy(ordinal_to_doy(x['end']))[0]
    lc_end = lc_start + len(lc) - 1
    if ts_start > lc_start:
        a = ts_start - lc_start
    else:
        a = 0
    if ts_end < lc_end:
        b = len(lc) - (lc_end - ts_end) -1
    else:
        b = len(lc) - 1
    if a <= b:
        return lc[int(a+b)/2]
    else:
        return x['class']


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='yatsm_r*.npz',
                        help='searching pattern')
    parser.add_argument('-s', '--start', action='store', type=int,
                        dest='start', default=2000, help='start year')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('map', default='./', help='stacked annual land cover')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start reverse classifying...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Stacked annual land cover maps from {}'.format(args.map))
    log.info('Start year: {}'.format(args.start))
    log.info('Saving in {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to reverse classify YATSM results
    reverse_classify(args.pattern, args.ori, args.map, args.des, args.start,
                        args.overwrite,args.recursive, args.batch)
