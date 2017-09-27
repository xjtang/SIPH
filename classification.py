""" Module for classification

    Args:
        -t (type): output map type
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination
        img: an example image to get the spatial reference

"""
import os
import sys
import argparse
import numpy as np

from osgeo import gdal

from .common import log, get_files, get_int, show_progress
from .common import constants as cons
from .io import stackGeo, cache2map, array2stack

def classification(ori, des, img, _type='cls', overwrite=False, recursive=False):
    """ Classify time series segments

    Args:
        ori (str): place to look for inputs
        des (str): place to save outputs
        img (str): path to example image
        _type (str): output map type
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading example image
        3: error in processing
        4: error in writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # get image spatial reference
    try:
        geo = stackGeo(img)
    except:
        log.error('Failed to read spatial reference from {}'.format(img))
        return 2

    # initialize output
    result = np.zeros((geo['lines'], geo['samples']), np.int16) + cons.NODATA
    count = 0

    # generate results
    for i in range(0,geo['lines']):
        try:
            # locate line cache file
            cache = get_files(ori, 'yatsm_r{}.npz'.format(i), recursive)
            # read line cache
            if len(cache) > 0:
                result[i,:] = cache2map(os.path.join(cache[0][0], cache[0][1]),
                                                        _type, geo['samples'])
                count += 1
            else:
                log.warning('Found no cache file for line {}'.format(i + 1))
                continue
        except:
            log.warning('Failed to process line {}.'.format(i + 1))
            continue
        progress = show_progress(i, geo['lines'], 5)
        if progress >= 0:
            log.info('{}% done.'.format(progress))

    # write output
    if _type == 'cls':
        output_type = gdal.GDT_Int16
    else:
        output_type = gdal.GDT_Int32
    if array2stack(result, geo, des, ['VNRT {} map'.format(_type)], cons.NODATA,
                    output_type, overwrite) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    log.info('{}/{} lines successful.'.format(count, geo['lines']))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', action='store', type=str,
                        dest='type', default='cls',
                        help='output map type')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    parser.add_argument('img', default='./', help='example image')
    args = parser.parse_args()

    # print logs
    log.info('Start classfying...')
    log.info('Cache file in {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Copy spatial reference from {}'.format(args.img))
    log.info('Making {} map.'.format(args.type))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to classify time series segments
    classification(args.ori, args.des, args.img, args.type, args.overwrite,
                args.recursive)
