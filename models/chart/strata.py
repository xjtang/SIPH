""" Module for creating strata from land cover change map

    Args:
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...io import stack2array, array2stack, stackGeo
from ...common import log, reclassify
from ...common import constants as cons


def create_strata(ori, des, overwrite=False):
    """ create stratification from map

    Args:
        ori (str): place to look for inputs
        des (str): place to save outputs
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error processing
        4: error writing output

    """
    # check if output exists, if not try to create one
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input map
    log.info('Reading input map...')
    try:
        geo = stackGeo(ori)
        array = stack2array(ori, 1, np.int32)
    except:
        log.error('Failed to read input map.')
        return 2

    # statifying
    log.info('Start creating strata...')
    try:
        strata = reclassify(array, cons.CHARTSCHEME)
    except:
        log.error('Failed to create strata.')
        return 3

    # writing output
    log.info('Writing output...')
    #try:
    if True:
        array2stack(strata.astype(np.int8), geo, des, ['strata'], 255,
                    gdal.GDT_Byte, overwrite)
    #except:
    #    log.error('Failed to write output to {}'.format(des))
    #    return 4

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
    log.info('Start creating strata...')
    log.info('Input map: {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to create strata
    create_strata(args.ori, args.des, args.overwrite)
