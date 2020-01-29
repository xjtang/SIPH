""" Module for reducing image bands

    Args:
        -m (method): how to reduce
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from scipy import stats
from osgeo import gdal

from ..common import log
from ..io import stackGeo, stack2array, array2stack, chkExist


def reducing(ori, des, method='mean', subset=[0,0], overwrite=False):
    """ stack raster layers

    Args:
        ori (str): input image
        des (str): output image
        method (str): reducing method
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error when processing
        4: error writing output

    """
    # check if output exists
    if chkExist(des, False, overwrite) > 0:
        return 1

    # locate files
    log.info('Reading input: {}'.format(ori))
    try:
        geo = stackGeo(ori)
        stack = stack2array(ori, [x for x in range(subset[0], subset[1]+1)])
        log.info('Total bands: {}'.format(stack.shape[2]))
    except:
        log.error('Failed to read input from: {}'.format(ori))
        return 2

    # reducing
    log.info('Reducing...')
    try:
        if method == 'mean':
            r = np.mean(stack, 2, dtype=np.int16)
        elif method == 'mode':
            r = np.squeeze(stats.mode(stack, 2)[0].astype(np.int16))
        elif method == 'unique':
            r = np.zeros((geo['lines'], geo['samples']), dtype=np.int16)
            for i in range(0, geo['lines']):
                for j in range(0, geo['samples']):
                    r[i, j] = len(np.unique(stack[i, j, :]))
        else:
            log.error('Unknown method: {}'.format(method))
            return 3
    except:
        log.error('Failed to reduce.')
        return 3

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(r, geo, des, ['{} reduced'.format(method)], 'NA',
                    gdal.GDT_Int16, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--method', action='store', type=str,
                        dest='method', default='mean',
                        help='reducing method')
    parser.add_argument('-s', '--subset', action='store', type=int, nargs=2,
                        dest='sub', default=[0,0], help='subset bands')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start reducing...')
    log.info('Input stack: {}'.format(args.ori))
    log.info('Reducing method: {}.'.format(args.method))
    if max(args.sub) > 0:
        log.info('Reading band {} to {}.'.format(args.sub[0], args.sub[1]))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old file.')

    # run function to reduce
    reducing(args.ori, args.des, args.method, args.sub, args.overwrite)
