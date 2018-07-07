""" Module for blending MODIS land cover product with YATSM results

    Args:
        -p (pattern): searching pattern
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        lc: stacked MODIS land cover map
        des: destination

"""
import os
import sys
import argparse

import numpy as np

from ...common import (log, get_files, manage_batch, enlarge, get_int,
                        ordinal_to_doy, ndarray_append, split_doy)
from ...io import stackGeo, stack2array, yatsm2pixels


def blend_lc(pattern, ori, lc, des, overwrite=False, recursive=False,
                batch=[1,1]):
    """ blend MODIS land cover product with YATSM results

    Args:
        pattern (str): searching pattern, e.g. yatsm_r*.npz
        ori (str): place to look for inputs
        lc (str): path to stacked MODIS land cover product
        des (str): output path and filename
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error when reading modis lc
        5: error when processing

    """
    # check if output exists, if not try to create one
    if not os.path.exists(des):
        log.warning('{} does not exist, trying to create one.'.format(des))
        try:
            os.makedirs(des)
        except:
            log.error('Cannot create output folder {}'.format(des))
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

    # read stacked MODIS land cover
    log.info('Reading stacked MODIS land cover: {}'.format(lc))
    try:
        geo = stackGeo(lc)
        lc_stack = stack2array(lc)
        lc_stack = np.kron(lc_stack, np.ones((2,2,1))).astype(lc_stack.dtype)
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
    log.info('Start blending pixels...')
    for yatsm in yatsm_list:
        try:
            blended = []
            py = get_int(yatsm[1])[0]
            log.info('Processing line {}'.format(py))
            pixels = yatsm2pixels(os.path.join(yatsm[0], yatsm[1]))
            for pixel in pixels:
                px = pixel[0]['px']
                blended.append(fuse_lc(ndarray_append(pixel[['px', 'py',
                                'start', 'end', 'break']], [('class', '<u2')]),
                                lc_stack[py, px, :]))
            np.savez(os.path.join(des, 'yatsm_lc_r{}.npz'.format(py)), blended)
            count += 1
        except:
            log.warning('Failed to process line {} pixel {}.'.format(py, px))
            continue

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


def fuse_lc(pixel, modis, modis_year=[2001, 2016]):
    """ blend MODIS land cover product with YATSM results on pixel level

    Args:
        pixel (list, ndarray): YATSM records of a pixel
        modis (list, int): MODIS land cover classes of a pixel
        modis_year (list, int): start and end year of MODIS land cover

    Returns:
        pixel (list, ndarray): pixel with land cover appended

    """
    for i, x in enumerate(pixel):
        _start = split_doy(ordinal_to_doy(x['start']))
        _end = split_doy(ordinal_to_doy(x['end']))
        _class = []
        _weight = []
        for y in range(_start[0], _end[0] + 1):
            if y in range(modis_year[0], modis_year[1] + 1):
                _class.append(x['class'])
            else:
                _class.append(-9999)
            nday = 365
            if y == _start[0]:
                nday -= _start[1]
            if y == _end[0]:
                nday -= 365 - _end[1]
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
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('lc', default='./', help='stacked MODIS land cover')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start blending...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Stacked MODIS land cover product from {}'.format(args.lc))
    log.info('Saving in {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to blend MODIS land cover product with YATSM results
    blend_lc(args.pattern, args.ori, args.lc, args.des, args.overwrite,
                args.recursive, args.batch)
