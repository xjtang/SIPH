""" Module for postprocessing VNRT result

    Args:
        -w (window): window size, how much extent out from the center pixel
        -t (threshold): clean up threshold
        -d (date): try to clean up the date images in the same folder as well
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, clean_up, get_files
from ...common import constants as cons
from ...io import stack2array, stackGeo, array2stack


def vnrt_postprocess(ori, des, w=1, t=2, d=False, overwrite=False):
    """ postprocess VNRT result

    Args:
        ori (str): place to look for inputs
        des (str): place to save outputs
        w (int): window size, how much extent out from the center pixel
        t (int): clean up threhold
        d (bool): try to clean up the date images, or not
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading input
        3: error during processing
        4: error when writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # reading input image
    log.info('Reading input image: {}'.format(ori))
    try:
        geo = stackGeo(ori)
        array = stack2array(ori, 1)
    except:
        log.error('Failed to read input image: {}'.format(ori))
        return 2

    # post-processing
    log.info('Start post-processing...')
    try:
        array2 = np.copy(array)
        array[array == cons.PC] = cons.CHANGE
        array = clean_up(array, w, t)
        array[(array == cons.CHANGE) & (array2 == cons.PC)] = cons.PC
        array2 = None
    except:
        log.error('Failed to clean up.')

    # clean up date images as well
    if d:
        log.info('Attempt to clean up date images...')
        _path = os.path.dirname(ori)
        d_list = get_files(_path,'*do*.tif')
        if len(d_list) > 0:
            for img in d_list:
                try:
                    img2 = stack2array(os.path.join(img[0],img[1]), 1, np.int32)
                    img2[(array!=cons.CHANGE) & (array!=cons.PC)] = cons.NODATA
                    if array2stack(img2, geo, os.path.join(img[0],
                                    '{}_clean.tif'.format(img[1][:-4])),
                                    ['Post-processed Date Image'], cons.NODATA,
                                    gdal.GDT_Int32, overwrite=overwrite) > 0:
                        log.warning('Failed to export {}'.format(img[1]))
                    log.info('Cleaned up {}'.format(img[1]))
                except:
                    log.warning('Failed to clean up {}'.format(img[1]))
        else:
            log.warning('Found no date image.')

    # writing output
    log.info('Writing output to: {}'.format(des))
    if array2stack(array, geo, des, 'Post-processed Map', cons.NODATA,
                    overwrite=overwrite) > 0:
        log.error('Faield to write output to {}'.format(des))

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--window', action='store', type=int,
                        dest='window', default=1,
                        help='window size, how much from center pixel')
    parser.add_argument('-t', '--threshold', action='store', type=int,
                        dest='threshold', default=2,
                        help='clean up threshold')
    parser.add_argument('-d', '--date', action='store_true',
                        help='look for date images in the same folder')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start postprocessing...')
    log.info('Input image {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Window size {}, clean up threshold {}.'.format(args.window,
                                                                args.threshold))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to preprocess data
    vnrt_postprocess(args.ori, args.des, args.window, args.threshold, args.date,
                        args.overwrite)
