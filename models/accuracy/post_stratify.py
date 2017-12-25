""" Module for post-stratify

    Args:
        -s (strata): strata value
        -d (dilations): dilation
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
from __future__ import division

import os
import sys
import argparse
import numpy as np

from osgeo import gdal

from ...io import stackGeo, array2stack, stack2array
from ...common import log, get_files, dilate
from ...common import constants as cons


def post_stratification(ori, des, strata=[1], dilation=1, overwrite=False):
    """ select sample from images

    Args:
        ori (str): input image
        des (str): output image
        strata (int/list): strata values to post stratify
        dilation (int/list): how many pixel to dilate
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error preprocessing
        3: error stratifying
        4: error writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read inputs
    log.info('Reading input image...')
    try:
        geo = stackGeo(ori)
        array = stack2array(ori, 1)
        total = (array != geo['nodata']).sum()
    except:
        log.error('Failed to read {}'.format(os.path.basename(ori)))
        return 2

    # pre-process
    log.info('Preprocessing input data...')
    try:
        array2 = np.zeros(array.shape, array.dtype)
        for i in strata:
            array2[array == i] = 1
    except:
        log.error('Failed to preprocess.')
        return 3

    # post-stratify
    log.info('Post-stratifying...')
    try:
        array3 = np.copy(array2)
        for i in range(0,dilation):
            array3 = dilate(array3)
            change = ((array3 > array2) & (array != geo['nodata'])).sum()
            log.info('Dilation: {}'.format(i + 1))
            log.info('Percentage: {:.1f}%'.format(change / total * 100))
    except:
        log.error('Failed to post-stratify.')
        return 4

    # write output
    log.info('Writing output...')
    array[(array3 > array2) & (array != geo['nodata'])] = array.max() + 1
    if array2stack(array, geo, des, ['Post-stratified Layer'], cons.NODATA,
                    gdal.GDT_Int16, overwrite) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 5

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--strata', action='store', type=int, nargs='+',
                        dest='strata', default=1, help='strata')
    parser.add_argument('-d', '--dilation', action='store', type=int,
                        dest='dilation', default=1, help='dilation')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start post-stratifying...')
    log.info('Input image: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    log.info('Strata value: {}'.format(args.strata))
    log.info('Dilation: {}'.format(args.dilation))
    if type(args.strata) == int:
        args.strata = [args.strata]
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to post-stratify
    post_stratification(args.ori, args.des, args.strata, args.dilation,
                        args.overwrite)
