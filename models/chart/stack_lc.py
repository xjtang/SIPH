""" Module for stacking MODIS land cover product

    Args:
        -p (pattern): searching pattern
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from osgeo import gdal

from ...common import log, get_files, nchange
from ...io import stackMerge, stackGeo, stack2array, array2stack


def modislc_stack(pattern, ori, des, overwrite=False, recursive=False):
    """ stack MODIS land cover product

    Args:
        pattern (str): searching pattern, e.g. M*tif
        ori (str): place to look for inputs
        des (str): place to save outputs
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error when processing

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
        lc_list = get_files(ori, pattern, recursive)
        lc_list = [os.path.join(x[0], x[1]) for x in lc_list]
        n = len(lc_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # stack file
    log.info('Stacking images...')
    try:
        stackMerge(lc_list, os.path.join(des, 'MODIS_LC_Stack.tif'),
                    gdal.GDT_Int16, overwrite)
    except:
        log.error('Failed to merge files.')
        return 4

    # calculate nchange
    log.info('Calculating nchange...')
    try:
        geo = stackGeo(os.path.join(des, 'MODIS_LC_Stack.tif'))
        lc = stack2array(os.path.join(des, 'MODIS_LC_Stack.tif'))
        nc = nchange(lc)
        array2stack(nc, geo, os.path.join(des, 'MODIS_LC_nchange.tif'),
                    ['MODIS LC nchange'], -9999, gdal.GDT_Int16, overwrite)
    except:
        log.error('Failed to calculate nchange.')
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='M*tif',
                        help='searching pattern')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start preprocessing...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to stack land cover product
    modislc_stack(args.pattern, args.ori, args.des, args.overwrite,
                    args.recursive)
