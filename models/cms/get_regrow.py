""" Module for summarizing regrow status

    Args:
        -p (pattern): searching pattern
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import constants as cons
from ...common import log, get_files, get_int
from ...io import stackGeo, stack2array, array2stack, chkExist


def regrow(pattern, ori, des, overwrite=False, recursive=False):
    """ figuring out when regrow started and ended

    Args:
        pattern (str): searching pattern, e.g. *tif
        ori (str): place to look for inputs
        des (str): path and file name of output
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error when processing
        5: error writing output

    """
    # check if output exists
    if chkExist(des, True) > 0:
        return 1

    # locate files
    log.info('Locating files...')
    try:
        img_list = get_files(ori, pattern, recursive)
        img_list = [os.path.join(x[0], x[1]) for x in img_list]
        n = len(img_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # get files in order
    log.info('Sorting files...')
    img_id = [get_int(x)[0] for x in img_list]
    img_list = [[img_list[x], img_id[x]] for x in np.argsort(img_id)]

    # initialize output
    log.info('Initializing output...')
    try:
        geo = stackGeo(img_list[0][0])
        result = np.zeros((geo['lines'], geo['samples'], 3),
                            np.int16) + 255
    except:
        log.error('Failed to initialize output.')
        return 4

    # work through maps
    log.info('Working through maps...')
    try:
        for i, img in enumerate(img_list):
            array = stack2array(img[0], 1, np.int8)
            array[(array == 1) & (result[:, :, 0] == 5)] = 5
            array[(array == 5) & (result[:, :, 0] == 1)] = 1
            array[(array == 1) & (result[:, :, 0] == 2)] = 5

            result[((array == 1) & (result[:, :, 0] == 255)), ] = (1, 255, 255)
            result[((array == 5) & (result[:, :, 0] == 255)), ] = (5, i, 255)
            result[((array != 5) & (result[:, :, 0] == 255)), ] = (2, 255, 255)

            result[((array == 1) & (result[:, :, 0] == 2)), ] = (5, i, 255)
            result[((array == 5) & (result[:, :, 0] == 2)), ] = (5, i, 255)

            result[((array != 5) & (result[:, :, 0] == 5)), 0:3:2] = (4, i)
            result[((array != 1) & (result[:, :, 0] == 1)), ] = (3, 255, 255)

        result[(result[:, :, 1] == 0), 0] = 6
    except:
        log.error('Failed during processing {}.'.format(img[0]))
        return 4

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(result[:, :, 0], geo, os.path.join(des, 'rg_cls.tif'),
                    'Class', 255, gdal.GDT_Byte, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write class to {}'.format(des))
        return 5
    if array2stack(result[:, :, 1], geo, os.path.join(des, 'rg_str.tif'),
                    'Class', 255, gdal.GDT_Byte, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write start to {}'.format(des))
        return 5
    if array2stack(result[:, :, 2], geo, os.path.join(des, 'rg_end.tif'),
                    'Class', 255, gdal.GDT_Byte, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write end to {}'.format(des))
        return 5

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='*tif',
                        help='searching pattern')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Analyzing images...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to analyze images
    regrow(args.pattern, args.ori, args.des, args.overwrite, args.recursive)
