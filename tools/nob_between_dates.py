""" Module for calculating number of clear observations between two dates

    Args:
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        img1: image of start date
        img2: image of end date
        ori: origin of cache files
        des: destination

"""
import os
import argparse
import numpy as np
import scipy.io as sio

from osgeo import gdal

from ..io import stack2array
from ..common import log, get_files


NODATA = -9999


def get_nob_between_dates(img1, img2, ori, des, overwrite=False,
                            recursive=False):
    """ Generage image of number of clear observation between two dates

    Args:
        img1 (str): path to image of start dates
        img2 (str): path to image of end dates
        ori (str): place to look for cache files
        des (str): place to save outputs
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        verbose (bool): verbose or not

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
        img = gdal.Open(img1, gdal.GA_ReadOnly)
        _proj = img.GetProjection()
        _geotrans = img.GetGeoTransform()
        img = None
        (lines, samples) = array1.shape
    except:
        log.error('Failed to read input stack {} and {}'.format(img1, img2))
        return 2

    # initialize output
    log.info('Initializing output...')
    try:
        result = np.zeros((lines, samples), np.int16) + NODATA
    except:
        log.error('Failed to initialize output of size {},{}.'.format(lines,
                    samples))
        return 3

    # loop through lines
    log.info('Calculating number of clear observations...')
    try:
        for i in range(0, lines):
            # locate line cache file
            cache_file = get_files(ori, 'ts*r{}.*'.format(i + 1), recursive)
            # read line cache
            if len(cache_file) > 0:
                cache = sio.loadmat(os.path.join(cache_file[0][0],
                                                    cache_file[0][1]))
            else:
                log.warning('Found no cache file for line {}'.format(i))
                continue
            # loop through samples
            for j in range(0, samples):
                # see if calculation is necessar
                date1 = array1[i][j]
                date2 = array2[i][j]
                if date1 > 1000000 and date2 > 1000000:
                    # calculate nob between the two dates
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
    except:
        log.error('Failed process line {}.'.format(i))
        return 4

    # write output
    log.info('Writing output: {}'.format(des))
    try:
        # initialize output
        _driver = gdal.GetDriverByName('GTiff')
        output = _driver.Create(des, samples, lines, 1, gdal.GDT_Int16)
        output.SetProjection(_proj)
        output.SetGeoTransform(_geotrans)
        output.GetRasterBand(1).SetNoDataValue(NODATA)
        # write output
        output.GetRasterBand(1).WriteArray(result)
        # assign band name
        output.GetRasterBand(1).SetDescription('Number of clear observations')
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('img1', default='./', help='image of start date')
    parser.add_argument('img2', default='./', help='image of end date')
    parser.add_argument('ori', default='./', help='origin of cache files')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start exporting image...')
    log.info('Cache in {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Start image: {}'.format(args.img1))
    log.info('End image: {}'.format(args.img2))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting existing image.')

    # run function to get nob between two dates
    get_nob_between_dates(args.img1, args.img2, args.ori, args.des,
                            args.overwrite, args.recursive)
