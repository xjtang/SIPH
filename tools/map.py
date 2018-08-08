""" Module for create map from a set of stacked images

    Args:
        -m (map): waht type of map
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ..common import constants as cons
from ..common import log, nchange
from ..io import stackGeo, stack2array, array2stack


def mapping(ori, des, map, overwrite=False, recursive=False):
    """ stack raster layers

    Args:
        ori (str): input stack
        des (str): output path and filename
        map (str): what type of map
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error when processing
        4: error writing output

    """
    # check if output exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # locate files
    log.info('Reading input: {}'.format(ori))
    try:
        geo = stackGeo(ori)
        stack = stack2array(ori)
    except:
        log.error('Failed to read input from: {}'.format(ori))
        return 2

    # mapping
    log.info('Processing...')
    try:
        if map == 'nchange':
            result = nchange(stack)
        else:
            log.error('Unknown map: {}'.format(map))
            return 3
    except:
        log.error('Failed to make {} map.'.format(map))
        return 3

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(result, geo, des, ['{} map'.format(map)], cons.NODATA,
                    gdal.GDT_Int16, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map', action='store', type=str,
                        dest='map', default='nchange',
                        help='searching pattern')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start mapping...')
    log.info('Input stack: {}'.format(args.ori))
    log.info('Making {} map.'.format(args.map))
    log.info('Saving as {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old file.')

    # run function to gnerate map
    mapping(args.ori, args.des, args.map, args.overwrite, args.recursive)
