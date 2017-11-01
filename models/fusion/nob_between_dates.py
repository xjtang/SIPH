""" Module for calculating number of clear observations between two dates

    Args:
        -p (pattern): searching pattern for cache file
        -f (file): image list file for yatsm cache
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        img1: image of start date
        img2: image of end date
        ori: origin of cache files
        des: destination

"""
import os
import sys
import argparse
import numpy as np
import scipy.io as sio

from osgeo import gdal

from ...io import stack2array, stackGeo, array2stack, csv2list
from ...common import log, get_files
from ...common import constants as cons


def get_nob_between_dates(pattern, _type, img1, img2, ori, des, overwrite=False,
                            recursive=False, _file='NA'):
    """ Generage image of number of clear observation between two dates

    Args:
        pattern (str): searching pattern for cache files
        _type (str): cache type, mat or npz
        img1 (str): path to image of start dates
        img2 (str): path to image of end dates
        ori (str): place to look for cache files
        des (str): output path and filename
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        _file (str): path to image list file for yatsm cache

    Returns:
        0: successful
        1: error due to des
        2: error reading input
        3: error during processing
        4: error during writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read input images
    log.info('Reading date images...')
    try:
        # read date image
        array1 = stack2array(img1, 1, np.int32)
        array2 = stack2array(img2, 1, np.int32)
        # get spatial reference
        geo = stackGeo(img1)
        (lines, samples) = array1.shape
    except:
        log.error('Failed to read input stack {} and {}'.format(img1, img2))
        return 2

    # initialize output
    log.info('Initializing output...')
    try:
        result = np.zeros((lines, samples), np.int16) + cons.NODATA
    except:
        log.error('Failed to initialize output of size {},{}.'.format(lines,
                    samples))
        return 3

    # loop through lines
    log.info('Calculating number of clear observations...')
    try:
        for i in range(0, lines):
            # locate line cache file
            if _type == 'mat':
                cache_file = get_files(ori, pattern.replace('[line]',
                                        str(i + 1)), recursive)
            else:
                cache_file = get_files(ori, pattern.replace('[line]', str(i)),
                                        recursive)
            # read line cache
            if len(cache_file) > 0:
                if _type == 'mat':
                    cache = sio.loadmat(os.path.join(cache_file[0][0],
                                                        cache_file[0][1]))
                else:
                    cache = np.load(os.path.join(cache_file[0][0],
                                                    cache_file[0][1]))
            else:
                log.warning('Found no cache file for line {}'.format(i))
                continue
            # loop through samples
            for j in range(0, samples):
                # see if calculation is necessar
                date1 = array1[i][j]
                date2 = array2[i][j]
                if date1 > cons.RESULT_MIN and date2 > cons.RESULT_MIN:
                    # calculate nob between the two dates
                    if _type == 'mat':
                        ts = cache['Data'][j,:]
                        dts = cache['Date'][:,0]
                        index1 = np.where(dts >= date1)[0][0]
                        index2 = np.where(dts >= date2)[0][0]
                        if date2 > date1:
                            ets = ts[index1:index2]
                            result[i, j] = sum(ets > 0)
                        elif date2 < date1:
                            ets = ts[index2:index1]
                            result[i, j] = -sum(ets > 0)
                        else:
                            result[i, j] = 0
                    else:
                        ts = cache['Y'][3, :, j]
                        dlist = csv2list(_file, True)
                        dts = np.asarray([x for x in dlist])
                        index1 = np.where(dts >= date1)[0][0]
                        index2 = np.where(dts >= date2)[0][0]
                        if date2 > date1:
                            ets = ts[index1:index2]
                            result[i, j] = sum(ets > 0)
                        elif date2 < date1:
                            ets = ts[index2:index1]
                            result[i, j] = -sum(ets > 0)
                        else:
                            result[i, j] = 0
    except:
        log.error('Failed process line {} sample {}.'.format(i + 1, j + 1))
        return 4

    # write output
    log.info('Writing output: {}'.format(des))
    if array2stack(result, geo, des, ['Number of clear observations'],
                    cons.NODATA, gdal.GDT_Int16, overwrite) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='ts*r[line].*mat',
                        help='searching pattern')
    parser.add_argument('-f', '--file', action='store', type=str, dest='file',
                        default='NA', help='image list')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('img1', default='./', help='image of start date')
    parser.add_argument('img2', default='./', help='image of end date')
    parser.add_argument('ori', default='./', help='origin of cache files')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # get type
    if args.pattern[-3:] == 'npz':
        _type = 'npz'
        if not os.path.isfile(args.file):
            log.error('Image list file does not exist: {}'.format(args.file))
            sys.exit(1)
    else:
        _type = 'mat'

    # print logs
    log.info('Start calculating nobs...')
    log.info('Cache in {}'.format(args.ori))
    log.info('Cache pattern {}'.format(args.pattern))
    log.info('Cache type: {}.'.format(_type))
    log.info('Saving in {}'.format(args.des))
    log.info('Start image: {}'.format(args.img1))
    log.info('End image: {}'.format(args.img2))
    if not args.file == 'NA':
        log.info('Image list file: {}'.format(args.file))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to get nob between two dates
    get_nob_between_dates(args.pattern, _type, args.img1, args.img2, args.ori,
                            args.des, args.overwrite, args.recursive, args.file)
