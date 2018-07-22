""" Module for figuring out when one class changed to another in series of maps

    Args:
        -p (pattern): searching pattern
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        classes: class a and class b
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import constants as cons
from ...common import log, get_files, get_int
from ...io import stackGeo, stack2array, array2stack


def atob(pattern, ori, des, _class, stack=False, overwrite=False,
            recursive=False):
    """ figuring out when one class changed to another in series of maps

    Args:
        pattern (str): searching pattern, e.g. *tif
        ori (str): place to look for inputs
        des (str): path and file name of output
        class (list, int): [class1, class2], -9999 for all other classes
        stack(bool): single stack input
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
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    if stack:
        img_list = [[os.path.dirname(ori),
                        os.path.basename(ori)] for i in range(0,
                        stackGeo(ori)['bands'])]
    else:
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
        result = np.zeros((geo['lines'],geo['samples']), np.int16) + cons.NODATA
    except:
        log.error('Failed to initialize output.')
        return 4

    # work through maps
    log.info('Working through maps...')
    try:
        for img in img_list:
            array = stack2array(img[0], 1, np.int8)
            if _class[0] == -9999:
                if geo['nodata'] != 'NA':
                    result[(array != _class[1]) & (array != geo['nodata'])] = 0
                else:
                    result[array != _class[1]] = 0
            else:
                result[array == _class[0]] = 0
            if _class[1] == -9999:
                result[(array != _class[0]) & (result == 0)] = img[1]
            else:
                result[(array == _class[1]) & ((result == 0) |
                        (result == cons.NODATA))] = img[1]
            result[result == img_list[0][1]] = 2
    except:
        log.error('Failed during processing {}.'.format(img[0]))
        return 4

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(result, geo, des,
                    ['From class {} to {}'.format(_class[0], _class[1])],
                    cons.NODATA, gdal.GDT_Int16, overwrite, 'GTiff',
                    ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write output to {}'.format(des))
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
    parser.add_argument('-s', '--stack', action='store_true',
                        help='input is a single stack, or not')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('classes', type=int, nargs=2, default=[1,-9999],
                        help='classes, class A and class B')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Analyzing images...')
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    log.info('From class {} to class {}.'.format(args.classes[0], args.classes[1]))
    if args.stack:
        log.info('Single stack input.')
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to analyze images
    atob(args.pattern, args.ori, args.des, args.classes, args.stack,
            args.overwrite, args.recursive)
