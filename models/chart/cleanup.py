""" Module for clean-up results

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log
from ...io import stack2array, stackGeo, array2stack


def clean_up(ori, des, overwrite=False):
    """ clean-up results

    Args:
        ori (str): path and filename of classification results
        des (str): place to save output map
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
    log.info('Reading input maps...')
    try:
        r = stack2array(ori)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(ori)
    except:
        log.error('Failed to read geo info.')
        return 2

    # refine classification results
    log.info('Cleaning up map...')
    try:
        r[r==1] = 2
        r[r==14] = 12
        r[r==8] = 9
    except:
        log.error('Failed to clean-up result.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(r, geo, des, 'NA', 255, gdal.GDT_Byte, overwrite)
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
    parser.add_argument('ori', default='./', help='classification results')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start clean-up...')
    log.info('Input map: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to refine clean-up result
    clean_up(args.ori, args.des, args.overwrite)
