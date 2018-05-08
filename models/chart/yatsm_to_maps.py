""" Module for generating maps from YATSM results

    Args:
        -t (type): output map type
        -o (option): map specific options
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination
        img: an example image to get the spatial reference

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, get_files, get_int, show_progress
from ...common import constants as cons
from ...io import stackGeo, yatsm2map, array2stack

def yatsm2map(ori, des, img, _type='cls', option=[], overwrite=False,
                recursive=False):
    """ Classify time series segments

    Args:
        ori (str): place to look for inputs
        des (str): output path and filename
        img (str): path to example image
        _type (str): output map type
        option (list): map specific options
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading example image
        3: error in writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # get image spatial reference
    log.info('Reading spatial reference from: {}'.format(img))
    try:
        geo = stackGeo(img)
    except:
        log.error('Failed to read spatial reference from {}'.format(img))
        return 2

    # initialize output
    log.info('Initializing output...')
    if (_type == 'change' or _type == 'nchange' or _type == 'class'):
        result = np.zeros((geo['lines'],geo['samples']), np.int16) + cons.NODATA
        output_type = gdal.GDT_Int16
    else:
        result = np.zeros((geo['lines'],geo['samples']), np.int32) + cons.NODATA
        output_type = gdal.GDT_Int32
    count = 0

    # generate results
    log.info('Start generating map...')
    for i in range(0, geo['lines']):
        try:
            # locate line cache file
            yatsm = get_files(ori, 'yatsm_r{}.npz'.format(i), recursive)
            # read line cache
            if len(yatsm) > 0:
                result[i,:] = yatsm2map(os.path.join(yatsm[0][0], yatsm[0][1]),
                                                        _type, geo['samples'],
                                                        option)
                count += 1
            else:
                log.warning('Found no YATSM file for line {}'.format(i + 1))
                continue
        except:
            log.warning('Failed to process line {}.'.format(i + 1))
            continue
        progress = show_progress(i, geo['lines'], 5)
        if progress >= 0:
            log.info('{}% done.'.format(progress))

    # write output
    log.info('Writing output to: {}'.format(des))
    if array2stack(result, geo, des, ['YATSM {} map'.format(_type)],
                    cons.NODATA, output_type, overwrite) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 3

    # done
    log.info('Process completed.')
    log.info('{}/{} lines successful.'.format(count, geo['lines']))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', action='store', type=str,
                        dest='type', default='change',
                        help='output map type')
    parser.add_argument('-o', '--option', action='store', type=int, nargs='+',
                        dest='option', default=[0],
                        help='map specific option')
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
    log.info('YATSM files in {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Copy spatial reference from {}'.format(args.img))
    log.info('Making {} map.'.format(args.type))
    log.info('Options: {}'.format(args.option))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to generatet maps from YATSM results
    yatsm2map(args.ori, args.des, args.img, args.type, args.option,
                args.overwrite, args.recursive)
