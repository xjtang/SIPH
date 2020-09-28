""" Module for track land cover classes over time

    Args:
        -p (pattern): searching pattern
        -m (mask): mask image
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from ...common import constants as cons
from ...common import log, get_files, get_int
from ...io import stack2array, chkExist


def tracking(pattern, ori, des, mask='NA', overwrite=False, recursive=False):
    """ track land cover classes over time

    Args:
        pattern (str): searching pattern, e.g. *tif
        ori (str): place to look for inputs
        des (str): path and file name of output
        mask (str): mask image
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file
        4: error reading mask
        5: error when processing
        6: error writing output

    """
    cls = [0, 2, 4, 5, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 25]
    lbl = 'NS,Ever,Deci,Mixed,Savanna,Grass,Werland,Ag,Urban,Barren,Rice,Plantation,Mangrove,Flooded,Aqua,Water'
    # check if output exists
    if not overwrite:
        if chkExist(des) > 0:
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
    img_id = [get_int(x)[1] for x in img_list]
    log.info('IDs: {}'.format(img_id))
    img_list = [[img_list[x], img_id[x]] for x in np.argsort(img_id)]

    # initialize output
    log.info('Initializing output...')
    try:
        result = np.zeros((n, len(cls)), np.int32)
    except:
        log.error('Failed to initialize output.')
        return 5

    # read mask
    if mask != 'NA':
        log.info('Applying mask...')
        try:
            mask2 = stack2array(mask, 1, np.int8)
        except:
            log.error('Failed to read mask from {}'.format(mask))
            return 4

    # work through maps
    log.info('Working through maps...')
    try:
        for i, img in enumerate(img_list):
            array = stack2array(img[0], 1, np.int8)
            if mask != 'NA':
                array[mask2 != 1] = 255
            for j, _class in enumerate(cls):
                result[i, j] = (array == _class).sum()
    except:
        log.error('Failed during processing {}.'.format(img[0]))
        return 5

    # write output
    log.info('Writing output: {}'.format(des))
    try:
        np.savetxt(des, result, delimiter=',', fmt='%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d',
                    header=lbl, comments='')
    except:
        log.error('Failed to write output to {}'.format(des))
        return 6

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='*tif',
                        help='searching pattern')
    parser.add_argument('-m', '--mask', action='store', type=str,
                        dest='mask', default='NA',
                        help='mask image')
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
    if args.mask != 'NA':
        log.info('Mask image: {}'.format(args.mask))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to analyze images
    tracking(args.pattern, args.ori, args.des, args.mask, args.overwrite,
                args.recursive)
