""" Module to reclassify the regrow image

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import constants as cons
from ...common import log
from ...io import stackGeo, stack2array, array2stack


def reclass_image(ori, des, overwrite=False):
    """ figuring out when one class changed to another in series of maps

    Args:
        ori (str): path and file name of input
        des (str): path and file name of output
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when processing
        3: error writing output

    """
    # check if output exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # initialize output
    log.info('Reading input...')
    try:
        geo = stackGeo(ori)
        array = stack2array(ori, 1, np.int16)
    except:
        log.error('Failed to read {}'.format(ori))
        return 2

    # loop through files
    log.info('Reclassifying...')
    try:
        array[array > 0] = 1000
        array[array <= 0] = 0
    except:
        log.error('Failed during processing.')
        return 3

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(array, geo, des, ['Regrowth'], cons.NODATA, gdal.GDT_Int16,
                    overwrite, 'GTiff', ['COMPRESS=PACKBITS']) > 0:
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
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Reclassify regrowth image...')
    log.info('Regrowth image: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to reclassify images
    reclass_image(args.ori, args.des, args.overwrite)
