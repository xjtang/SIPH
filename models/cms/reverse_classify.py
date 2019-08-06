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
        lc_stack = stack2array(lc)
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
            reved = []
            py = get_int(yatsm[1])[0]
            log.info('Processing line {}'.format(py))
            pixels = yatsm2pixels(os.path.join(yatsm[0], yatsm[1]))
            others = np.load(os.path.join(yatsm[0], yatsm[1]))
            for pixel in pixels:
                px = pixel[0]['px']
                reved.append(rev_class(pixel, lc_stack[py, px, :], _start))
            np.savez(os.path.join(des, 'yatsm_r{}.npz'.format(py)),
                        record=reved, classes=others['classes'],
                        version=others['version'])
            count += 1
        except:
            log.warning('Failed to process line {} pixel {}.'.format(py, px))
            continue

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


def rev_class(pixel, lc, lc_start):
    """ blend MODIS land cover product with YATSM results on pixel level

    Args:
        pixel (list, ndarray): YATSM records of a pixel
        lc (list, int): annual land cover classes of a pixel
        lc_start (int): start year of annual land cover

    Returns:
        pixel (list, ndarray): pixel with land cover modified

    """
    for i, x in enumerate(pixel):
        ts_start = split_doy(ordinal_to_doy(x['start']))
        ts_end = split_doy(ordinal_to_doy(x['end']))
        lc_end = lc_start + len(pixel) - 1
        _class = []
        _weight = []
        for y in range(ts_start[0], ts_end[0] + 1):
            if y in range(lc_start, lc_end + 1):
                _class.append(lc[y - lc_start])
            else:
                _class.append(-9999)
            nday = 365
            if y == ts_start[0]:
                nday -= ts_start[1]
            if y == ts_end[0]:
                nday -= 365 - ts_end[1]
            if nday >= 270:
                _weight.append(100)
            elif nday < 90:
                _weight.append(1)
            else:
                _weight.append(51)
        pixel[i]['class'] = get_class(_class, _weight)
    return pixel


def get_class(_class, _weight):
    """ figure our class of time segment based on annual class and weight

    Args:
        _class (list, int): annual class
        _weight (list, int): weight of annual class

    Returns:
        class2 (int): class of the segment

    """
    c_class = []
    c_weight = []
    for i, x in enumerate(_class):
        if x not in c_class:
            c_class.append(x)
            c_weight.append(_weight[i])
        else:
            c_weight[c_class.index(x)] += _weight[i]
    class2 = c_class[np.argmax(c_weight)]
    return class2


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
