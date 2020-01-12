""" Module for creating strata map from land cover maps of two dates

    Args:
        --overwrite: overwrite or not
        map1: map of year 1
        map2: map of year 2
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...io import stack2array, array2stack, stackGeo, chkExist
from ...common import log
from ...common import constants as cons


def create_strata(map1, map2, des, overwrite=False):
    """ create stratification from map

    Args:
        map1 (str): map of year 1
        map2 (str): map of year 2
        des (str): place to save outputs
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error processing
        4: error writing output

    """
    c2s = cons.CLASS2STRATA

    # check if output exists, if not try to create one
    if chkExist(des) > 0:
        return 1

    # read input map
    log.info('Reading input map...')
    try:
        geo = stackGeo(map1)
        array1 = stack2array(map1, 1, np.int8)
        array2 = stack2array(map2, 1, np.int8)
    except:
        log.error('Failed to read input map.')
        return 2

    # initialize output
    log.info('Initializing output...')
    result = np.zeros((geo['lines'], geo['samples']), np.int8) + 255

    # statifying
    log.info('Start creating strata...')
    try:
        for i in range(0, geo['lines']):
            for j in range(0, geo['samples']):
                if array1[i, j] == array2[i, j]:
                    if array1[i, j] > 0:
                        result[i, j] = c2s[array1[i, j]]
                else:
                    L1 = c2s[array1[i, j]]
                    L2 = c2s[array2[i, j]]
                    if ((L2 == 2) & (L1 != 2)):
                        result[i, j] = 10
                    elif L2 == 9:
                        result[i, j] = 11
                    elif L2 == 6:
                        result[i, j] = 12
                    elif ((L1 in [1, 3]) & (L2 in [4, 5, 7, 8])):
                        result[i, j] = 13
                    elif ((L1 in [2, 4, 5, 6, 7, 8]) & (L2 in [1, 3])):
                        result[i, j] = 14
                    else:
                        result[i, j] = 15
    except:
        log.error('Failed to create strata.')
        return 3

    # writing output
    log.info('Writing output...')
    try:
        array2stack(result, geo, des, ['strata'], 255, gdal.GDT_Byte, overwrite,
                    'GTiff', ['COMPRESS=LZW'])
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('map1', default='./', help='map1')
    parser.add_argument('map2', default='./', help='map2')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start creating strata...')
    log.info('Input map 1: {}'.format(args.map1))
    log.info('Input map 2: {}'.format(args.map2))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to create strata
    create_strata(args.map1, args.map2, args.des, args.overwrite)
