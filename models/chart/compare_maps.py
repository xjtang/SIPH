""" Module for comparing two MODIS land cover map

    Args:
        -b (bitshift): how many bits to shift for the first map
        -s (stable): convert stable to 0 or not
        --overwrite: overwrite or not
        map1: map 1
        map2: map 2
        des: destination

"""
import os
import sys
import argparse

from osgeo import gdal

from ...common import log, get_files, manage_batch
from ...io import stack2array, stackGeo, array2stack


def compare_maps(map1, map2, des, bitshift=3, stable=True, overwrite=False):
    """ compare MODIS land cover maps

    Args:
        map1 (str): path and filename of first map
        map2 (str): path and filename of second map
        des (str): place to save output map
        bitshift (int): how many bits to shift the first map class
        stable (bool): convert stable to 0 or not
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading inputs
        3: error during processing
        4: error writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input image
    log.info('Reading input maps.')
    try:
        array1 = stack2array(map1, 1)
        array2 = stack2array(map2, 1)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(map1)
    except:
        log.error('Failed to read geo info.')
        return 2

    # compare maps
    log.info('Comparing maps')
    try:
        array3 = array1 * (10**bitshift) + array2
        if stable:
            array3[array1==array2] = 0
        if geo['nodata'] != 'NA':
            array3[array1==geo['nodata']] = 255
            array3[array2==geo['nodata']] = 255
    except:
        log.error('Failed to compare maps.')
        return 3

    # write output
    log.info('Writing output: {}'.format(des))
    try:
        array2stack(array3, geo, des, ['Change'], 255, gdal.GDT_Int32,
                    overwrite)
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bitshift', action='store', type=int,
                        dest='bit', default=3, help='how many bit to shift')
    parser.add_argument('-s', '--stable', action='store_true',
                        help='stable to 0 or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('map1', default='./', help='map1')
    parser.add_argument('map2', default='./', help='map2')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start comparing...')
    log.info('Map 1 from {}'.format(args.map1))
    log.info('Map 2 from {}'.format(args.map2))
    log.info('Saving as {}'.format(args.des))
    log.info('Bit shift: {}'.format(args.bit))
    if args.stable:
        log.info('Convert stable to 0.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to compare maps
    compare_maps(args.map1, args.map2, args.des, args.bit, args.stable,
                    args.overwrite)
