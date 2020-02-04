""" Module for converting land cover to rooting depth

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
from ...io import stack2array, stackGeo, array2stack, chkExist
from ...common import constants as cons


def lc2rd(ori, des, overwrite=False):
    """ land cover to rooting depth results

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
    if chkExist(des, False, overwrite) > 0:
        return 1

    # read input image
    log.info('Reading input maps...')
    try:
        geo = stackGeo(ori)
        lc = stack2array(ori)
    except:
        log.error('Failed to read input maps.')
        return 2

    # converting
    log.info('Converting to rooting depth...')
    try:
        C2R = cons.CLASS2RD
        rd = np.zeros(lc.shape, np.int16) - 1
        for x in range(0, len(C2R)):
            rd[lc == x] = C2R[x]
    except:
        log.error('Failed to convert to rooting depth.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(rd, geo, des, 'Rooting Depth', -1, gdal.GDT_Int16,
                    overwrite, 'GTiff', ['COMPRESS=LZW'])
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
    log.info('Start converting...')
    log.info('Input map: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to convert land cover to rooting depth
    lc2rd(args.ori, args.des, args.overwrite)
